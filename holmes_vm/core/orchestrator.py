#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator for Holmes VM setup
"""

import os
import time
import threading
from typing import List, Tuple, Callable, Any, Optional

from holmes_vm.core.config import Config
from holmes_vm.core.logger import Logger
from holmes_vm.utils.notifications import show_notification
from holmes_vm.installers.base import get_registry
from holmes_vm.installers.chocolatey import ChocolateyInstaller
from holmes_vm.installers.powershell import PowerShellInstaller
from holmes_vm.installers.functions import (
    NetworkCheckInstaller, ChocolateySetupInstaller, PipUpgradeInstaller,
    WallpaperInstaller, AppearanceInstaller, PrepareDesktopGroupsInstaller,
    CreateShortcutInstaller, DisableDefenderInstaller
)


class SetupOrchestrator:
    """Orchestrates the Holmes VM setup process"""

    def __init__(self, config: Config, logger: Logger, args: Any):
        self.config = config
        self.logger = logger
        self.args = args
        self.registry = get_registry()

    def build_steps_from_selection(self, selected_ids: List[str]) -> List[Tuple[str, Callable]]:
        """Build installation steps from selected tool IDs"""
        steps: List[Tuple[str, Callable]] = []
        # Admin/Windows check is done early in setup.py before UI loads
        prep = PrepareDesktopGroupsInstaller(self.config, self.logger, self.args)
        steps.append((prep.get_name(), lambda inst=prep: inst.install()))

        for tool_id in selected_ids:
            tool_config = self.config.get_tool_by_id(tool_id)
            if not tool_config:
                self.logger.warn(f"Tool not found in config: {tool_id}")
                continue

            # Skip-if-installed: check if tool exe already exists on disk
            if not getattr(self.args, 'force_reinstall', False):
                if self._is_already_installed(tool_id, tool_config):
                    tool_name = tool_config.get('name', tool_id)
                    self.logger.success(f"{tool_name} already installed, skipping.")
                    continue

            installer_type = tool_config.get('installer_type')

            if installer_type == 'function':
                installer_id = self.config.get_function_installer_id(tool_id)
                installer = self.registry.get_installer(installer_id, self.config, self.logger, self.args)
                if installer:
                    steps.append((installer.get_name(), lambda inst=installer: inst.install()))
                else:
                    self.logger.warn(f"Installer not found: {installer_id}")

            elif installer_type == 'chocolatey':
                choco = self.config.get_choco_params(tool_id) or {}
                installer = ChocolateyInstaller(
                    self.config, self.logger, self.args,
                    choco.get('name'), choco.get('tool_name'), choco.get('version'), choco.get('install_args'), choco.get('suppress_default_args')
                )

                # Prepare optional shortcut creator
                desktop_group = tool_config.get('desktop_group')
                shortcut_installer = None
                if desktop_group and desktop_group.lower() != 'runtimes':
                    shortcut_installer = CreateShortcutInstaller(
                        self.config, self.logger, self.args, tool_id
                    )

                # Single combined step: install then create shortcut
                def _do_install_and_shortcut(inst=installer, sc_inst=shortcut_installer):
                    if not inst.install():
                        raise RuntimeError(f"{inst.get_name()} failed")
                    if sc_inst:
                        try:
                            sc_inst.install()
                        except Exception:
                            pass

                steps.append((installer.get_name(), _do_install_and_shortcut))

            elif installer_type == 'powershell':
                ps = self.config.get_powershell_params(tool_id) or {}
                ps_args = ps.get('args', '') or ''
                if tool_id == 'eztools':
                    log_dir = getattr(self.args, 'log_dir', None)
                    if log_dir:
                        ps_args = (ps_args + f" -LogDir '{log_dir}'").strip()

                desktop_group = tool_config.get('desktop_group')
                if desktop_group:
                    shortcut_category = desktop_group
                    # Place bundle shortcuts in subfolders inside Bundles
                    if desktop_group.lower() == 'bundles':
                        shortcut_category = f"{desktop_group}\\{tool_config.get('name')}"
                    ps_args = (ps_args + f" -ShortcutCategory '{shortcut_category}'").strip()

                # Large downloads get longer timeout (Ghidra, Autopsy, EZ Tools, Sysinternals)
                big_tools = {'ghidra', 'autopsy', 'eztools', 'sysinternals'}
                tool_timeout = 600 if tool_id in big_tools else 180

                installer = PowerShellInstaller(
                    self.config, self.logger, self.args,
                    ps.get('script_path'), ps.get('function_name'), ps.get('tool_name'), ps_args,
                    timeout=tool_timeout
                )

                # Optional second-chance shortcut creation in same step
                sc_inst = None
                if desktop_group and desktop_group.lower() != 'runtimes':
                    sc_inst = CreateShortcutInstaller(
                        self.config, self.logger, self.args, tool_id
                    )

                def _do_ps_and_shortcut(inst=installer, sc=sc_inst):
                    if not inst.install():
                        raise RuntimeError(f"{inst.get_name()} failed")
                    if sc:
                        try:
                            sc.install()
                        except Exception:
                            pass

                steps.append((installer.get_name(), _do_ps_and_shortcut))

        return steps

    def _is_already_installed(self, tool_id: str, tool_config: dict) -> bool:
        """Check if a tool is already installed by looking for its executable."""
        shortcut = tool_config.get('shortcut') or {}
        mode = shortcut.get('mode')

        if mode == 'exe_candidates':
            for c in shortcut.get('exe_candidates', []):
                path = c
                if path.startswith('${LOCALAPPDATA}'):
                    la = os.environ.get('LOCALAPPDATA', '')
                    path = path.replace('${LOCALAPPDATA}', la)
                if os.path.exists(path):
                    return True

        elif mode == 'search_exe':
            exe_name = shortcut.get('exe_name', '')
            for root in shortcut.get('search_roots', []):
                if os.path.isdir(root):
                    for dirpath, _, files in os.walk(root):
                        if exe_name in files:
                            return True

        elif mode == 'folder_all':
            for folder in shortcut.get('folders', []):
                if os.path.isdir(folder) and os.listdir(folder):
                    return True

        elif mode == 'eztools':
            root = shortcut.get('root', '')
            if os.path.isdir(root) and os.listdir(root):
                return True

        return False

    def run_steps(self, steps: List[Tuple[str, Callable]], ui=None, cancel_event: Optional[threading.Event] = None) -> int:
        """Run installation steps. Returns number of failures.

        Failed steps are skipped automatically so the remaining tools
        can still be installed.
        """
        if not steps:
            self.logger.warn('No steps to execute.')
            return 0

        total = len(steps)
        start = time.time()
        failures = 0
        skipped = 0

        for i, (name, action) in enumerate(steps, start=1):
            if cancel_event and cancel_event.is_set():
                self.logger.warn('Cancelled by user before next step.')
                skipped = total - i + 1
                break

            if ui:
                ui.enqueue(('step_hdr', i, total, name))
                ui.enqueue(('status', f'[{i}/{total}] {name}'))
                ui.enqueue(('progress_to', int((i - 1) * 100 / total)))

            self.logger.current_step = name
            self.logger.info(f"{name}")

            step_start = time.time()
            success = True
            try:
                action()
                step_elapsed = time.time() - step_start
                self.logger.success(f"{name} completed ({step_elapsed:.1f}s).")
            except Exception as e:
                success = False
                failures += 1
                step_elapsed = time.time() - step_start
                self.logger.error(f"{name} failed ({step_elapsed:.1f}s): {e}")
                if i < total:
                    self.logger.info(f"Skipping to next step...")

            if ui:
                ui.enqueue(('step_result', i, success))
                # Show what's coming next
                if i < total:
                    next_name = steps[i][0]
                    ui.enqueue(('status', f'Next: {next_name}'))

            done_fraction = i / max(1, total)
            elapsed = time.time() - start
            eta = (elapsed / done_fraction) - elapsed if done_fraction > 0 else None

            if ui:
                ui.set_eta(eta)
                ui.enqueue(('progress_to', int(i * 100 / total)))

        self.logger.current_step = None
        elapsed = time.time() - start
        mm, ss = divmod(int(elapsed), 60)
        if failures:
            self.logger.warn(f'{failures}/{total} step(s) failed. Total time: {mm}m {ss}s.')
        else:
            self.logger.success(f'All {total} steps completed in {mm}m {ss}s.')
        self._notify_completion(total, failures)
        return failures

    def run_steps_console(self, steps: List[Tuple[str, Callable]]) -> int:
        """Run installation steps in console mode. Returns number of failures.

        Failed steps are skipped automatically.
        """
        if not steps:
            self.logger.warn('No steps to execute.')
            return 0

        total = len(steps)
        start = time.time()
        failures = 0

        for i, (name, action) in enumerate(steps, start=1):
            self.logger.current_step = name
            self.logger.info(f"[{i}/{total}] {name}")

            step_start = time.time()
            try:
                action()
                step_elapsed = time.time() - step_start
                self.logger.success(f"{name} completed ({step_elapsed:.1f}s).")
            except Exception as e:
                failures += 1
                step_elapsed = time.time() - step_start
                self.logger.error(f"{name} failed ({step_elapsed:.1f}s): {e}")
                self.logger.info(f"Skipping to next step...")

        self.logger.current_step = None
        elapsed = time.time() - start
        mm, ss = divmod(int(elapsed), 60)
        if failures:
            self.logger.warn(f'{failures}/{total} step(s) failed. Total time: {mm}m {ss}s.')
        else:
            self.logger.success(f'All {total} steps completed in {mm}m {ss}s.')
        self._notify_completion(total, failures)
        return failures

    def _notify_completion(self, total: int, failures: int):
        """Send a native OS notification when setup finishes."""
        try:
            if failures == 0:
                show_notification(
                    'Holmes VM Setup Complete',
                    f'All {total} steps completed successfully.'
                )
            else:
                show_notification(
                    'Holmes VM Setup Finished',
                    f'{total - failures}/{total} steps succeeded, {failures} failed.'
                )
        except Exception:
            pass  # Notifications are best-effort

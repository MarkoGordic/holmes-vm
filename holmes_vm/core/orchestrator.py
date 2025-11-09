#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator for Holmes VM setup
"""

import time
import threading
from typing import List, Tuple, Callable, Any, Optional

from holmes_vm.core.config import Config
from holmes_vm.core.logger import Logger
from holmes_vm.utils.system import is_admin, is_windows
from holmes_vm.installers.base import get_registry
from holmes_vm.installers.chocolatey import ChocolateyInstaller
from holmes_vm.installers.powershell import PowerShellInstaller
from holmes_vm.installers.functions import (
    NetworkCheckInstaller, ChocolateySetupInstaller, PipUpgradeInstaller,
    WallpaperInstaller, AppearanceInstaller, PrepareDesktopGroupsInstaller, CreateShortcutInstaller
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
        steps.append(('Assert Windows/Admin', lambda: self._assert_windows_admin()))
        prep = PrepareDesktopGroupsInstaller(self.config, self.logger, self.args)
        steps.append((prep.get_name(), lambda inst=prep: inst.install()))
        
        for tool_id in selected_ids:
            tool_config = self.config.get_tool_by_id(tool_id)
            if not tool_config:
                self.logger.warn(f"Tool not found in config: {tool_id}")
                continue
            
            installer_type = tool_config.get('installer_type')
            
            if installer_type == 'function':
                installer_id = self.config.get_function_installer_id(tool_id)
                # Previously skipped organize_desktop; now enabled
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
                    inst.install()
                    if sc_inst:
                        try:
                            sc_inst.install()
                        except Exception as _:
                            # Shortcut creation failure should not fail the whole step
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
                
                installer = PowerShellInstaller(
                    self.config, self.logger, self.args,
                    ps.get('script_path'), ps.get('function_name'), ps.get('tool_name'), ps_args
                )
                
                # Optional second-chance shortcut creation in same step
                sc_inst = None
                if desktop_group and desktop_group.lower() != 'runtimes':
                    sc_inst = CreateShortcutInstaller(
                        self.config, self.logger, self.args, tool_id
                    )
                
                def _do_ps_and_shortcut(inst=installer, sc=sc_inst):
                    inst.install()
                    if sc:
                        try:
                            sc.install()
                        except Exception:
                            pass
                
                steps.append((installer.get_name(), _do_ps_and_shortcut))
        
        return steps
    
    def _assert_windows_admin(self):
        """Assert that we're running on Windows with admin privileges"""
        if not is_windows():
            raise RuntimeError('Windows-only setup')
        if not is_admin():
            raise RuntimeError('Run as Administrator')
    
    def run_steps(self, steps: List[Tuple[str, Callable]], ui=None, cancel_event: Optional[threading.Event] = None):
        """Run installation steps"""
        total = len(steps)
        start = time.time()
        
        for i, (name, action) in enumerate(steps, start=1):
            if cancel_event and cancel_event.is_set():
                self.logger.warn('Cancelled by user before next step.')
                break
            
            if ui:
                ui.enqueue(('step_hdr', i, total, name))
                ui.enqueue(('status', 'Working'))
                ui.enqueue(('progress_to', int((i - 1) * 100 / total)))
            
            self.logger.current_step = name
            self.logger.info(f"{name}")  # zero-width spaces ensure uniqueness for tagging
            
            success = True
            try:
                action()
                self.logger.success(f"{name} completed.")
            except Exception as e:
                success = False
                self.logger.error(f"{name} failed: {e}")
            
            if ui:
                ui.enqueue(('step_result', i, success))
            
            done_fraction = i / max(1, total)
            elapsed = time.time() - start
            eta = (elapsed / done_fraction) - elapsed if done_fraction > 0 else None
            
            if ui:
                ui.set_eta(eta)
                ui.enqueue(('progress_to', int(i * 100 / total)))
        
        self.logger.current_step = None
    
    def run_steps_console(self, steps: List[Tuple[str, Callable]]):
        """Run installation steps in console mode"""
        total = len(steps)
        
        for i, (name, action) in enumerate(steps, start=1):
            self.logger.current_step = name
            self.logger.info(f"[{i}/{total}] {name}")
            
            try:
                action()
                self.logger.success(f"{name} completed.")
            except Exception as e:
                self.logger.error(f"{name} failed: {e}")
        
        self.logger.current_step = None

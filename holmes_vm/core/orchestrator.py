#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator for Holmes VM setup
"""

import time
import threading
from typing import List, Tuple, Callable, Any, Optional

from ..core.config import Config
from ..core.logger import Logger
from ..utils.system import is_admin, is_windows
from ..installers.base import get_registry
from ..installers.chocolatey import ChocolateyInstaller
from ..installers.powershell import PowerShellInstaller
from ..installers.functions import (
    NetworkCheckInstaller, ChocolateySetupInstaller, PipUpgradeInstaller,
    WallpaperInstaller, AppearanceInstaller, PinTaskbarInstaller
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
        steps = []
        
        # Always assert platform/admin
        steps.append(('Assert Windows/Admin', lambda: self._assert_windows_admin()))
        
        # Process each selected tool
        for tool_id in selected_ids:
            tool_config = self.config.get_tool_by_id(tool_id)
            if not tool_config:
                self.logger.warn(f"Tool not found in config: {tool_id}")
                continue
            
            installer_type = tool_config.get('installer_type')
            
            if installer_type == 'function':
                # Function-based installer
                installer_id = tool_config.get('installer')
                installer = self.registry.get_installer(installer_id, self.config, self.logger, self.args)
                if installer:
                    steps.append((installer.get_name(), lambda inst=installer: inst.install()))
                else:
                    self.logger.warn(f"Installer not found: {installer_id}")
            
            elif installer_type == 'chocolatey':
                # Chocolatey package installer
                package_name = tool_config.get('package_name')
                tool_name = tool_config.get('name')
                installer = ChocolateyInstaller(
                    self.config, self.logger, self.args,
                    package_name, tool_name
                )
                steps.append((installer.get_name(), lambda inst=installer: inst.install()))
            
            elif installer_type == 'powershell':
                # PowerShell script installer
                script_path = tool_config.get('script_path')
                function_name = tool_config.get('function_name')
                tool_name = tool_config.get('name')
                ps_args = tool_config.get('args', '')
                
                # Add LogDir argument if installing EZ Tools
                if tool_id == 'eztools':
                    log_dir = getattr(self.args, 'log_dir', None)
                    if log_dir:
                        ps_args = f"-LogDir '{log_dir}'"
                
                installer = PowerShellInstaller(
                    self.config, self.logger, self.args,
                    script_path, function_name, tool_name, ps_args
                )
                steps.append((installer.get_name(), lambda inst=installer: inst.install()))
            
            # Handle post-install actions
            post_install = tool_config.get('post_install', [])
            for action in post_install:
                action_type = action.get('type')
                
                if action_type == 'pin_taskbar':
                    path = action.get('path')
                    tool_name = tool_config.get('name')
                    installer = PinTaskbarInstaller(
                        self.config, self.logger, self.args,
                        path, tool_name
                    )
                    steps.append((installer.get_name(), lambda inst=installer: inst.install()))
                
                elif action_type == 'pin_taskbar_multi':
                    # Try multiple paths for pinning
                    paths = action.get('paths', [])
                    tool_name = tool_config.get('name')
                    for path in paths:
                        installer = PinTaskbarInstaller(
                            self.config, self.logger, self.args,
                            path, tool_name
                        )
                        steps.append((
                            f"Pin {tool_name} (attempt)",
                            lambda inst=installer: inst.install()
                        ))
        
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
            self.logger.info(f"{name}…")
            
            t0 = time.time()
            try:
                action()
                self.logger.success(f"{name} completed.")
            except Exception as e:
                self.logger.error(f"{name} failed: {e}")
            
            t1 = time.time()
            done_fraction = i / max(1, total)
            elapsed = t1 - start
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
            self.logger.info(f"[{i}/{total}] {name}…")
            
            try:
                action()
                self.logger.success(f"{name} completed.")
            except Exception as e:
                self.logger.error(f"{name} failed: {e}")
        
        self.logger.current_step = None

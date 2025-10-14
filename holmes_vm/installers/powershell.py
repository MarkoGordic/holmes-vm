#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerShell script installers
"""

import os
from .base import BaseInstaller, register_installer
from ..utils.system import run_powershell, import_common_module_and, dot_source_and


@register_installer('powershell')
class PowerShellInstaller(BaseInstaller):
    """Installer that runs PowerShell scripts"""
    
    def __init__(self, config, logger, args, script_path: str, function_name: str, tool_name: str, ps_args: str = ''):
        super().__init__(config, logger, args)
        self.script_path = script_path
        self.function_name = function_name
        self.tool_name = tool_name
        self.ps_args = ps_args
    
    def get_name(self) -> str:
        return f"Install {self.tool_name}"
    
    def install(self) -> bool:
        """Run PowerShell installer script"""
        self.logger.info(f'Installing {self.tool_name}...')
        
        ps1_full_path = os.path.join(self.config.repo_dir, self.script_path)
        
        if not os.path.exists(ps1_full_path):
            self.logger.error(f"Script not found: {ps1_full_path}")
            return False
        
        args = self.ps_args
        if self.is_what_if_mode() and '-WhatIf' not in args:
            args = (args + ' -WhatIf').strip()
        
        # Load common module, then dot-source the installer script, then call the function
        code = import_common_module_and(
            dot_source_and(ps1_full_path, f"{self.function_name} {args}"),
            self.config.module_path
        )
        
        res = run_powershell(code, cwd=self.config.repo_dir)
        
        if res.returncode != 0:
            self.logger.warn(f"{self.function_name} returned {res.returncode}: {res.stderr.strip()}")
            return False
        else:
            self.logger.success(f"{self.tool_name} completed.")
            return True

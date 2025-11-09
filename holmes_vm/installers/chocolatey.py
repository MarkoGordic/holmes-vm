#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chocolatey package installer
"""

from .base import BaseInstaller, register_installer
from ..utils.system import run_powershell, import_common_module_and


@register_installer('chocolatey')
class ChocolateyInstaller(BaseInstaller):
    """Installer for Chocolatey packages"""
    
    def __init__(self, config, logger, args, package_name: str, tool_name: str, version: str | None = None, install_args: str | None = None, suppress_default_args: bool = False):
        super().__init__(config, logger, args)
        self.package_name = package_name
        self.tool_name = tool_name
        self.version = version
        self.install_args = install_args
        self.suppress_default_args = suppress_default_args
    
    def get_name(self) -> str:
        return f"Install {self.tool_name}"
    
    def install(self) -> bool:
        """Install Chocolatey package"""
        self.logger.info(f'Installing {self.tool_name} via Chocolatey...')
        
        args = f"-Name '{self.package_name}'"
        if self.version:
            args += f" -Version '{self.version}'"
        if self.should_force_reinstall():
            args += ' -ForceReinstall'
        if self.is_what_if_mode():
            args += ' -WhatIf'
        if self.install_args:
            # pass through explicit install args
            args += f" -InstallArguments '{self.install_args}'"
        elif self.suppress_default_args:
            # suppress default, do nothing
            args += ' -SuppressDefaultInstallArgs'
        # else allow module to add default arguments automatically
        
        code = import_common_module_and(
            f"Install-ChocoPackage {args} | Out-Null",
            self.config.module_path
        )
        
        res = run_powershell(code)
        
        if res.returncode != 0:
            self.logger.warn(f"{self.tool_name} install returned {res.returncode}: {res.stderr.strip()}")
            return False
        else:
            self.logger.success(f"{self.tool_name} installed successfully.")
            return True

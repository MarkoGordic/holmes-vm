#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chocolatey package installer
"""

from typing import Optional
from .base import BaseInstaller, register_installer
from ..utils.system import run_powershell_streamed, import_common_module_and


@register_installer('chocolatey')
class ChocolateyInstaller(BaseInstaller):
    """Installer for Chocolatey packages"""

    def __init__(self, config, logger, args, package_name: str, tool_name: str, version: Optional[str] = None, install_args: Optional[str] = None, suppress_default_args: bool = False):
        super().__init__(config, logger, args)
        self.package_name = package_name
        self.tool_name = tool_name
        self.version = version
        self.install_args = install_args
        self.suppress_default_args = suppress_default_args

    def get_name(self) -> str:
        return f"Install {self.tool_name}"

    def install(self) -> bool:
        """Install Chocolatey package with live progress output"""
        self.logger.info(f'Installing {self.tool_name} via Chocolatey...')

        args = f"-Name '{self.package_name}'"
        if self.version:
            args += f" -Version '{self.version}'"
        if self.should_force_reinstall():
            args += ' -ForceReinstall'
        if self.is_what_if_mode():
            args += ' -WhatIf'
        if self.install_args:
            args += f" -InstallArguments '{self.install_args}'"

        code = import_common_module_and(
            f"Install-ChocoPackage {args}",
            self.config.module_path
        )

        res = run_powershell_streamed(code, logger=self.logger)

        if res.returncode != 0:
            stderr = res.stderr.strip()
            if 'timed out' in stderr.lower():
                self.logger.error(f"{self.tool_name} timed out. The download or install may be stuck.")
            elif 'not found' in stderr.lower() or 'no results' in stderr.lower():
                self.logger.error(f"Package '{self.package_name}' not found in Chocolatey. Check package name in config/tools.json.")
            else:
                self.logger.warn(f"{self.tool_name} install failed: {stderr[:200]}")
            return False
        else:
            self.logger.success(f"{self.tool_name} installed.")
            return True

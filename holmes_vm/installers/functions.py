#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function-based installers (Python implementations)
"""

import os
import sys
import shutil
import subprocess
from .base import BaseInstaller, register_installer
from ..utils.system import run_powershell, import_common_module_and, check_network


@register_installer('network_check')
class NetworkCheckInstaller(BaseInstaller):
    """Network connectivity check"""
    
    def get_name(self) -> str:
        return "Network connectivity"
    
    def install(self) -> bool:
        """Check network connectivity"""
        self.logger.info('Checking network connectivity...')
        
        urls = ['https://www.google.com/generate_204', 'https://github.com']
        ok = 0
        
        for url in urls:
            try:
                import urllib.request
                with urllib.request.urlopen(url, timeout=7) as resp:
                    if 200 <= resp.status < 400:
                        ok += 1
                        self.logger.success(f'Reachable: {url}')
                    else:
                        self.logger.warn(f'Unexpected status {resp.status} for {url}')
            except Exception as e:
                self.logger.warn(f'Not reachable: {url} ({e})')
        
        self.logger.info(f'Network connectivity summary: {ok}/{len(urls)} reachable')
        return ok > 0


@register_installer('ensure_choco')
class ChocolateySetupInstaller(BaseInstaller):
    """Ensure Chocolatey is installed"""
    
    def get_name(self) -> str:
        return "Ensure Chocolatey"
    
    def install(self) -> bool:
        """Ensure Chocolatey is installed"""
        self.logger.info('Ensuring Chocolatey...')
        
        code = import_common_module_and('Ensure-Chocolatey', self.config.module_path)
        res = run_powershell(code)
        
        if res.returncode != 0:
            self.logger.warn(f"Chocolatey setup returned {res.returncode}: {res.stderr.strip()}")
            return False
        else:
            self.logger.success('Chocolatey is ready.')
            return True


@register_installer('upgrade_pip')
class PipUpgradeInstaller(BaseInstaller):
    """Upgrade pip and core Python tools"""
    
    def get_name(self) -> str:
        return "Upgrade pip/setuptools/wheel"
    
    def install(self) -> bool:
        """Upgrade pip and core tools"""
        self.logger.info('Upgrading pip and core tools...')
        
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-U', 'pip', 'setuptools', 'wheel'],
                check=False, capture_output=True, text=True
            )
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-U', 'pipx', 'virtualenv'],
                check=False, capture_output=True, text=True
            )
            self.logger.success('Pip and core tools upgraded.')
            return True
        except Exception as e:
            self.logger.warn(f'pip upgrade failed: {e}')
            return False


@register_installer('install_wallpaper')
class WallpaperInstaller(BaseInstaller):
    """Install and apply wallpaper"""
    
    def get_name(self) -> str:
        return "Copy and apply wallpaper"
    
    def install(self) -> bool:
        """Copy and apply wallpaper"""
        src = os.path.join(self.config.assets_dir, 'wallpaper.jpg')
        
        if not os.path.exists(src):
            self.logger.warn('Wallpaper not found in assets; skipping.')
            return False
        
        dest_dir = r'C:\\Tools\\Wallpapers'
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, 'holmes-wallpaper.jpg')
        
        try:
            shutil.copyfile(src, dest)
            self.logger.success(f'Wallpaper copied to {dest}')
        except Exception as e:
            self.logger.warn(f'Failed to copy wallpaper: {e}')
            return False
        
        # Apply wallpaper
        self.logger.info('Applying wallpaper...')
        code = import_common_module_and(
            f"Set-Wallpaper -ImagePath '{dest}' -Style Fill",
            self.config.module_path
        )
        res = run_powershell(code)
        
        if res.returncode != 0:
            self.logger.warn(f'Apply wallpaper returned {res.returncode}: {res.stderr.strip()}')
            return False
        else:
            self.logger.success('Wallpaper applied.')
            return True


@register_installer('set_appearance')
class AppearanceInstaller(BaseInstaller):
    """Apply Windows appearance settings"""
    
    def get_name(self) -> str:
        return "Apply Windows appearance"
    
    def install(self) -> bool:
        """Apply Windows appearance settings"""
        self.logger.info('Applying Windows appearance...')
        
        code = import_common_module_and(
            "Set-WindowsAppearance -DarkMode -AccentHex '#0078D7' -ShowAccentOnTaskbar -EnableTransparency -ApplyForAllUsers -RestartExplorer",
            self.config.module_path
        )
        res = run_powershell(code)
        
        if res.returncode != 0:
            self.logger.warn(f'Appearance setup returned {res.returncode}: {res.stderr.strip()}')
            return False
        else:
            self.logger.success('Windows appearance applied.')
            return True


@register_installer('pin_taskbar')
class PinTaskbarInstaller(BaseInstaller):
    """Pin application to taskbar"""
    
    def __init__(self, config, logger, args, path: str, tool_name: str):
        super().__init__(config, logger, args)
        self.path = path
        self.tool_name = tool_name
    
    def get_name(self) -> str:
        return f"Pin {self.tool_name}"
    
    def install(self) -> bool:
        """Pin application to taskbar"""
        self.logger.info(f'Pinning {self.tool_name} to taskbar...')
        
        code = import_common_module_and(
            f"Pin-TaskbarItem -Path '{self.path}'",
            self.config.module_path
        )
        res = run_powershell(code)
        
        if res.returncode == 0:
            self.logger.success(f'{self.tool_name} pinned (or already pinned).')
            return True
        else:
            self.logger.warn(f'Failed to pin {self.tool_name}.')
            return False

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function-based installers (Python implementations)
"""

import os
import sys
import shutil
import subprocess
from typing import Optional, List, Dict, Tuple
from holmes_vm.installers.base import BaseInstaller, register_installer
from holmes_vm.utils.system import run_powershell, import_common_module_and


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
                with urllib.request.urlopen(url, timeout=7) as resp:  # nosec B310
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
    """Apply Windows appearance settings with Sherlock Holmes dark theme"""
    
    def get_name(self) -> str:
        return "Apply Windows appearance (Dark Mode)"
    
    def install(self) -> bool:
        """Apply Windows appearance settings with dark theme"""
        self.logger.info('Applying Sherlock Holmes dark theme...')
        
        # Victorian brown accent color: #A0826D
        code = import_common_module_and(
            "Set-WindowsAppearance -DarkMode -AccentHex '#A0826D' -ShowAccentOnTaskbar -EnableTransparency -ApplyForAllUsers -RestartExplorer",
            self.config.module_path
        )
        res = run_powershell(code)
        
        if res.returncode != 0:
            self.logger.warn(f'Appearance setup returned {res.returncode}: {res.stderr.strip()}')
            return False
        else:
            self.logger.success('Dark theme with Victorian brown accent applied.')
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


@register_installer('organize_desktop')
class OrganizeDesktopInstaller(BaseInstaller):
    """Organize Desktop shortcuts into folders per category"""

    def get_name(self) -> str:
        return "Organize Desktop shortcuts"

    def _get_desktop_path(self) -> str:
        # Prefer USERPROFILE\\Desktop
        userprofile = os.environ.get('USERPROFILE') or os.path.expanduser('~')
        return os.path.join(userprofile, 'Desktop')

    def _collect_items(self) -> List[Tuple[str, Dict[str, str]]]:
        """Return list of (group_name, item_dict) that have desktop_group"""
        pairs: List[Tuple[str, Dict[str, str]]] = []
        for cat in self.config.get_categories():
            for item in cat.get('items', []):
                group = item.get('desktop_group')
                if group:
                    pairs.append((group, item))
        return pairs

    def _derive_tokens(self, item: Dict[str, str]) -> List[str]:
        # Prefer explicit keywords
        keywords = item.get('desktop_keywords') or []
        if keywords:
            return [k.lower() for k in keywords if isinstance(k, str) and k]
        # Derive from name: strip parentheses and split
        import re
        name = (item.get('name') or '').lower()
        name = re.sub(r"\([^)]*\)", "", name)  # remove (...) parts
        parts = re.split(r"[^a-z0-9]+", name)
        tokens = [p for p in parts if len(p) >= 3]
        # Also include id
        iid = (item.get('id') or '').lower()
        if iid:
            tokens.append(iid)
        # De-duplicate while preserving order
        seen = set()
        out: List[str] = []
        for t in tokens:
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out

    def _safe_move(self, src: str, dst_dir: str) -> Optional[str]:
        try:
            os.makedirs(dst_dir, exist_ok=True)
            base = os.path.basename(src)
            dst = os.path.join(dst_dir, base)
            # Avoid overwrite
            if os.path.exists(dst):
                name, ext = os.path.splitext(base)
                i = 2
                while True:
                    cand = os.path.join(dst_dir, f"{name} ({i}){ext}")
                    if not os.path.exists(cand):
                        dst = cand
                        break
                    i += 1
            if self.is_what_if_mode():
                self.logger.info(f"[what-if] Move '{src}' -> '{dst}'\n")
                return dst
            shutil.move(src, dst)
            return dst
        except Exception as e:
            self.logger.warn(f"Failed to move '{src}' to '{dst_dir}': {e}")
            return None

    def install(self) -> bool:
        desktop = self._get_desktop_path()
        if not os.path.isdir(desktop):
            self.logger.warn('Desktop path not found; skipping organization.')
            return False

        pairs = self._collect_items()
        if not pairs:
            self.logger.info('No desktop grouping metadata present; nothing to organize.')
            return True

        # Current desktop entries
        try:
            entries = [os.path.join(desktop, e) for e in os.listdir(desktop)]
        except Exception as e:
            self.logger.warn(f'Cannot enumerate Desktop: {e}')
            return False

        moved_any = False
        desktop_dirs = [p for p in entries if os.path.isdir(p)]

        # Move folders whose names match tokens (contains), but skip target group folders
        for group, item in pairs:
            group_dir = os.path.join(desktop, group)
            tokens = self._derive_tokens(item)
            os.makedirs(group_dir, exist_ok=True)
            for d in list(desktop_dirs):
                if os.path.normcase(d) == os.path.normcase(group_dir):
                    continue  # do not move the target folder itself
                base = os.path.basename(d).lower()
                if any(tok in base for tok in tokens):
                    # Only move if folder currently sits directly on Desktop
                    if os.path.dirname(d) == desktop:
                        target = os.path.join(group_dir, os.path.basename(d))
                        try:
                            if self.is_what_if_mode():
                                self.logger.info(f"[what-if] Move folder '{d}' -> '{target}'\n")
                            else:
                                shutil.move(d, target)
                            moved_any = True
                            # Update lists to avoid repeated moves
                            entries = [os.path.join(desktop, e) for e in os.listdir(desktop)]
                            desktop_dirs = [p for p in entries if os.path.isdir(p)]
                        except Exception as e:
                            self.logger.warn(f"Failed moving folder '{d}': {e}")

        # Refresh file list for shortcuts
        try:
            entries = [os.path.join(desktop, e) for e in os.listdir(desktop)]
        except Exception:
            pass

        # Move shortcuts (.lnk, .url) whose names contain tokens
        for group, item in pairs:
            group_dir = os.path.join(desktop, group)
            tokens = self._derive_tokens(item)
            for path in list(entries):
                lower = path.lower()
                if not (lower.endswith('.lnk') or lower.endswith('.url')):
                    continue
                base = os.path.basename(lower)
                if any(tok in base for tok in tokens):
                    dst = self._safe_move(path, group_dir)
                    if dst:
                        moved_any = True
                        try:
                            entries.remove(path)
                        except ValueError:
                            pass

        if moved_any:
            self.logger.success('Desktop shortcuts organized into folders.')
        else:
            self.logger.info('No desktop items matched for organization.')
        return True

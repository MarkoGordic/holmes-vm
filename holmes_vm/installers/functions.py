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


@register_installer('prepare_desktop_groups')
class PrepareDesktopGroupsInstaller(BaseInstaller):
    """Create category desktop group folders at start so shortcuts land directly there."""

    def get_name(self) -> str:
        return "Prepare Desktop category folders"

    def _get_desktop_path(self) -> str:
        userprofile = os.environ.get('USERPROFILE') or os.path.expanduser('~')
        return os.path.join(userprofile, 'Desktop')

    def install(self) -> bool:
        desktop = self._get_desktop_path()
        if not os.path.isdir(desktop):
            self.logger.warn('Desktop path not found; skipping desktop group preparation.')
            return False
        groups: List[str] = []
        for cat in self.config.get_categories():
            for item in cat.get('items', []):
                g = item.get('desktop_group')
                if g and g not in groups:
                    groups.append(g)
        if not groups:
            self.logger.info('No desktop groups defined in config; nothing to prepare.')
            return True
        created = 0
        for g in groups:
            path = os.path.join(desktop, g)
            try:
                if self.is_what_if_mode():
                    self.logger.info(f"[what-if] Create folder '{path}'")
                else:
                    os.makedirs(path, exist_ok=True)
                created += 1
            except Exception as e:
                self.logger.warn(f"Failed to create '{path}': {e}")
        if created:
            self.logger.success(f"Prepared {created} desktop group folder(s).")
        else:
            self.logger.info('No new desktop group folders created.')
        return True


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
        stopwords = {
            'tool', 'tools', 'suite', 'viewer', 'view', 'windows', 'window',
            'analysis', 'forensics', 'forensic', 'browser', 'browsers',
            'bundle', 'bundles', 'runtime', 'dependencies', 'desktop'
        }
        name = (item.get('name') or '').lower()
        name = re.sub(r"\([^)]*\)", "", name)  # remove (...) parts
        parts = re.split(r"[^a-z0-9]+", name)
        tokens = [p for p in parts if len(p) >= 3 and p not in stopwords]
        # Also include id
        iid = (item.get('id') or '').lower()
        if iid:
            iid_parts = re.split(r"[^a-z0-9]+", iid)
            for tok in iid_parts:
                if len(tok) >= 3 and tok not in stopwords:
                    tokens.append(tok)
        # De-duplicate while preserving order
        seen = set()
        out: List[str] = []
        for t in tokens:
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out

    def _build_group_tokens(self, pairs: List[Tuple[str, Dict[str, str]]]) -> List[Tuple[str, List[str]]]:
        out_map: Dict[str, Tuple[str, List[str]]] = {}
        for group, item in pairs:
            key = group.lower()
            if key not in out_map:
                out_map[key] = (group, [])
            current_group, tokens = out_map[key]
            for tok in self._derive_tokens(item):
                if tok not in tokens:
                    tokens.append(tok)
            out_map[key] = (current_group, tokens)
        return list(out_map.values())

    def _pick_group_for_entry(self, entry_name: str, group_tokens: List[Tuple[str, List[str]]]) -> Optional[str]:
        name = entry_name.lower()
        best_group: Optional[str] = None
        best_score = 0
        for group, tokens in group_tokens:
            if not tokens:
                continue
            score = sum(len(tok) for tok in tokens if tok in name)
            if score > best_score:
                best_group = group
                best_score = score
        # Keep threshold above noise from tiny accidental matches.
        if best_score < 4:
            return None
        return best_group

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
        group_tokens = self._build_group_tokens(pairs)
        group_dirs = {group: os.path.join(desktop, group) for group, _ in group_tokens}
        for group_dir in group_dirs.values():
            os.makedirs(group_dir, exist_ok=True)

        desktop_dirs = [p for p in entries if os.path.isdir(p)]
        protected_dirs = {os.path.normcase(p) for p in group_dirs.values()}
        for d in list(desktop_dirs):
            if os.path.normcase(d) in protected_dirs:
                continue
            if os.path.dirname(d) != desktop:
                continue
            chosen = self._pick_group_for_entry(os.path.basename(d), group_tokens)
            if not chosen:
                continue
            dst = self._safe_move(d, group_dirs[chosen])
            if dst:
                moved_any = True

        # Refresh file list for shortcuts
        try:
            entries = [os.path.join(desktop, e) for e in os.listdir(desktop)]
        except Exception:
            pass

        # Move shortcuts (.lnk, .url) using best category token score
        for path in list(entries):
            lower = path.lower()
            if not (lower.endswith('.lnk') or lower.endswith('.url')):
                continue
            chosen = self._pick_group_for_entry(os.path.basename(lower), group_tokens)
            if not chosen:
                continue
            dst = self._safe_move(path, group_dirs[chosen])
            if dst:
                moved_any = True

        if moved_any:
            self.logger.success('Desktop shortcuts organized into folders.')
        else:
            self.logger.info('No desktop items matched for organization.')
        return True


@register_installer('create_shortcut')
class CreateShortcutInstaller(BaseInstaller):
    """Create shortcut for a single tool immediately after installation.
    This runs after each tool is installed, not at the end.
    """

    def __init__(self, config, logger, args, tool_id: str):
        super().__init__(config, logger, args)
        self.tool_id = tool_id

    def get_name(self) -> str:
        tool_config = self.config.get_tool_by_id(self.tool_id)
        tool_name = tool_config.get('name') if tool_config else self.tool_id
        return f"Create shortcut for {tool_name}"

    def _desktop(self) -> str:
        return os.path.join(os.environ.get('USERPROFILE') or os.path.expanduser('~'), 'Desktop')

    def _ensure_dir(self, path: str):
        if self.is_what_if_mode():
            self.logger.info(f"[what-if] mkdir {path}")
            return
        os.makedirs(path, exist_ok=True)

    def _ps_create_shortcut(self, target: str, shortcut_dir: str, name: Optional[str] = None, working_dir: Optional[str] = None) -> bool:
        base = name or os.path.splitext(os.path.basename(target))[0]
        lnk = os.path.join(shortcut_dir, f"{base}.lnk")
        wd = working_dir or os.path.dirname(target)
        
        # Escape single quotes in paths for PowerShell
        target_escaped = target.replace("'", "''")
        lnk_escaped = lnk.replace("'", "''")
        wd_escaped = wd.replace("'", "''")
        base_escaped = base.replace("'", "''")
        
        code = import_common_module_and(
            f"$shell=New-Object -ComObject WScript.Shell; $lnk='{lnk_escaped}'; $sc=$shell.CreateShortcut($lnk); $sc.TargetPath='{target_escaped}'; $sc.WorkingDirectory='{wd_escaped}'; $sc.WindowStyle=1; $sc.Description='{base_escaped}'; $sc.Save()",
            self.config.module_path
        )
        if self.is_what_if_mode():
            self.logger.info(f"[what-if] shortcut -> {lnk} -> {target}")
            return True
        res = run_powershell(code)
        ok = res.returncode == 0
        if ok:
            self.logger.success(f"Shortcut created: {os.path.basename(lnk)}")
        else:
            self.logger.warn(f"Failed to create shortcut for {target}: {res.stderr.strip()}")
        return ok

    def _ps_shortcuts_from_folder(self, folder: str, dest: str, filter_pat: str = '*.exe') -> bool:
        # Escape single quotes for PowerShell
        folder_escaped = folder.replace("'", "''")
        dest_escaped = dest.replace("'", "''")
        filter_escaped = filter_pat.replace("'", "''")
        
        code = import_common_module_and(
            f"New-ShortcutsFromFolder -Folder '{folder_escaped}' -Filter '{filter_escaped}' -ShortcutDir '{dest_escaped}' -WorkingDir '{folder_escaped}'",
            self.config.module_path
        )
        if self.is_what_if_mode():
            self.logger.info(f"[what-if] shortcuts from {folder} -> {dest} ({filter_pat})")
            return True
        res = run_powershell(code)
        ok = res.returncode == 0
        if ok:
            self.logger.success(f"Shortcuts created from {os.path.basename(folder)}")
        else:
            self.logger.warn(f"Failed creating shortcuts from {folder}: {res.stderr.strip()}")
        return ok

    def install(self) -> bool:
        tool_config = self.config.get_tool_by_id(self.tool_id)
        if not tool_config:
            self.logger.warn(f"Tool config not found for {self.tool_id}")
            return False
        
        desktop_group = tool_config.get('desktop_group')
        # Skip shortcut creation entirely for Runtime Dependencies category items
        if desktop_group and desktop_group.lower() == 'runtimes':
            return True
        if not desktop_group:
            # No desktop group means no shortcut needed
            return True
        
        tool_name = tool_config.get('name') or self.tool_id
        desktop = self._desktop()
        
        # Determine destination directory (Bundles get subfolder per tool)
        if desktop_group.lower() == 'bundles':
            dest_dir = os.path.join(desktop, desktop_group, tool_name)
        else:
            dest_dir = os.path.join(desktop, desktop_group)
        
        self._ensure_dir(dest_dir)
        
        # Get shortcut metadata for this tool
        meta = self.config.get_shortcut_meta(self.tool_id) or {}
        mode = meta.get('mode')
        
        if mode == 'exe_candidates':
            display = meta.get('display_name') or tool_name
            candidates = []
            for c in meta.get('exe_candidates', []):
                if c.startswith('${LOCALAPPDATA}'):
                    la = os.environ.get('LOCALAPPDATA', '')
                    candidates.append(c.replace('${LOCALAPPDATA}', la))
                else:
                    candidates.append(c)
            exe = next((p for p in candidates if os.path.exists(p)), None)
            if exe:
                return self._ps_create_shortcut(exe, dest_dir, display)
            else:
                self.logger.info(f"Executable not found for {tool_name} (may not be installed yet)")
                return True
                
        elif mode == 'search_exe':
            exe_name = meta.get('exe_name') or ''
            roots = meta.get('search_roots', [])
            exe = None
            for r in roots:
                if not os.path.exists(r):
                    continue
                for root, _, files in os.walk(r):
                    if exe_name in files:
                        exe = os.path.join(root, exe_name)
                        break
                if exe:
                    break
            if exe:
                return self._ps_create_shortcut(exe, dest_dir, meta.get('display_name') or tool_name)
            else:
                self.logger.info(f"Executable not found for {tool_name} (may not be installed yet)")
                return True
                
        elif mode == 'folder_all':
            made_any = False
            for folder in meta.get('folders', []):
                if os.path.isdir(folder):
                    made_any |= self._ps_shortcuts_from_folder(folder, dest_dir, meta.get('filter', '*.exe'))
            if not made_any:
                self.logger.info(f"No shortcuts created for {tool_name} (folder not found or empty)")
            return True
            
        elif mode == 'eztools':
            root = meta.get('root')
            order = meta.get('order', [])
            filter_pat = meta.get('filter', '*.exe')
            if root and os.path.isdir(root):
                priority_dirs = []
                for sub in order:
                    folder = os.path.join(root, sub)
                    if os.path.isdir(folder):
                        priority_dirs.append(folder)
                
                if priority_dirs:
                    dirs_escaped = [d.replace("'", "''") for d in priority_dirs]
                    dirs_str = "', '".join(dirs_escaped)
                    dest_escaped = dest_dir.replace("'", "''")
                    filter_escaped = filter_pat.replace("'", "''")
                    
                    code = import_common_module_and(
                        f"$priorityDirs = @('{dirs_str}'); $seen = @{{}}; $shell = New-Object -ComObject WScript.Shell; foreach ($dir in $priorityDirs) {{ Get-ChildItem -Path $dir -Recurse -Filter '{filter_escaped}' -File -ErrorAction SilentlyContinue | ForEach-Object {{ $name = $_.Name; if (-not $seen.ContainsKey($name)) {{ $lnk = Join-Path '{dest_escaped}' ($name -replace '\\.exe$', '') + '.lnk'; $sc = $shell.CreateShortcut($lnk); $sc.TargetPath = $_.FullName; $sc.WorkingDirectory = $_.Directory.FullName; $sc.WindowStyle = 1; $sc.Description = $_.BaseName; $sc.Save(); $seen[$name] = $true }} }} }}",
                        self.config.module_path
                    )
                    if not self.is_what_if_mode():
                        res = run_powershell(code)
                        if res.returncode == 0:
                            self.logger.success(f"EZ Tools shortcuts created")
                            return True
                        else:
                            self.logger.warn(f"Failed to create EZ Tools shortcuts: {res.stderr.strip()}")
                            return False
                    else:
                        self.logger.info(f"[what-if] eztools shortcuts from {priority_dirs} -> {dest_dir}")
                        return True
            self.logger.info(f"EZ Tools not found (may not be installed yet)")
            return True
        else:
            # No shortcut metadata - nothing to do
            return True

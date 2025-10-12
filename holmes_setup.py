#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Holmes VM Setup (Python UI)
- Dark-mode minimal Tkinter UI (no Microsoft Forms)
- Unified progress + logs
- Orchestrates existing PowerShell installers and helpers
- Continues on errors; logs everything to ProgramData
"""

import os
import sys
import ctypes
import subprocess
import threading
import queue
import time
from datetime import datetime
import argparse
import itertools

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import scrolledtext
except Exception:
    tk = None
    ttk = None
    scrolledtext = None

APP_NAME = "Holmes VM Setup"
LOG_DIR_DEFAULT = os.path.join(os.environ.get('ProgramData', 'C:/ProgramData'), 'HolmesVM', 'Logs')
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.path.join(REPO_DIR, 'modules', 'Holmes.Common.psm1')
UTIL_DIR = os.path.join(REPO_DIR, 'util')
ASSETS_DIR = os.path.join(REPO_DIR, 'assets')

# Colors (dark scheme)
COLOR_BG = '#0B1220'
COLOR_FG = '#E5E7EB'
COLOR_MUTED = '#94A3B8'
COLOR_ACCENT = '#1D4ED8'
COLOR_INFO = '#7DD3FC'
COLOR_WARN = '#FBBF24'
COLOR_ERROR = '#F87171'
COLOR_SUCCESS = '#34D399'

class Logger:
    def __init__(self, log_file, ui=None):
        self.log_file = log_file
        self.ui = ui
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self._lock = threading.Lock()
        self.current_step = None  # optional context injected by runner

    def _write_file(self, line):
        with self._lock:
            with open(self.log_file, 'a', encoding='utf-8', errors='ignore') as f:
                f.write(line)

    def log(self, level, msg):
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        ctx = f"[{self.current_step}]" if self.current_step else ""
        line = f"[{ts}][{level.upper()}]{ctx} {msg}\n"
        try:
            self._write_file(line)
        except Exception:
            pass
        if self.ui:
            self.ui.enqueue(('log', level.lower(), line))
        # Also echo to console
        print(line, end='')

    def info(self, msg):
        self.log('INFO', msg)

    def warn(self, msg):
        self.log('WARN', msg)

    def error(self, msg):
        self.log('ERROR', msg)

    def success(self, msg):
        self.log('SUCCESS', msg)

class UI:
    def __init__(self, title):
        if tk is None:
            raise RuntimeError('Tkinter not available; run in console mode')
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry('900x600')
        self.root.configure(bg=COLOR_BG)
        try:
            self.root.iconbitmap(False)
        except Exception:
            pass

        self.queue = queue.Queue()
        self._anim_target = 0
        self._anim_job = None
        self._start_time = time.time()
        self._last_eta = '—'
        self._filters = { 'info': True, 'warn': True, 'error': True, 'success': True }

        # Title
        self.title_lbl = tk.Label(self.root, text='Setting up Holmes VM', fg=COLOR_FG, bg=COLOR_BG,
                                  font=('Segoe UI', 14, 'bold'))
        self.title_lbl.place(x=20, y=18)

        # Status
        self.status_lbl = tk.Label(self.root, text='Initializing', fg=COLOR_MUTED, bg=COLOR_BG,
                                   font=('Segoe UI', 10))
        self.status_lbl.place(x=20, y=54)

        # Spinner
        self._spinner_frames = list('⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏')
        self._spinner_index = 0
        self.spinner_lbl = tk.Label(self.root, text=self._spinner_frames[0], fg=COLOR_ACCENT, bg=COLOR_BG,
                                    font=('Segoe UI', 12, 'bold'))
        self.spinner_lbl.place(x=860, y=18)

        # Progress
        self.progress = ttk.Progressbar(self.root, orient='horizontal', length=820, mode='determinate')
        self.progress.place(x=20, y=80)
        try:
            style = ttk.Style()
            style.theme_use('default')
            style.configure('TProgressbar', troughcolor=COLOR_BG, background=COLOR_ACCENT, thickness=12)
        except Exception:
            pass

        # Log box
        self.log_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', bg=COLOR_BG,
                                                 fg=COLOR_FG, font=('Consolas', 10))
        self.log_box.place(x=20, y=146, width=860, height=400)
        # Tags for colors
        self.log_box.tag_config('info', foreground=COLOR_INFO)
        self.log_box.tag_config('warn', foreground=COLOR_WARN)
        self.log_box.tag_config('error', foreground=COLOR_ERROR)
        self.log_box.tag_config('success', foreground=COLOR_SUCCESS)

        # Footer: elapsed / ETA and filters
        self.elapsed_lbl = tk.Label(self.root, text='Elapsed: 00:00 • ETA: —', fg=COLOR_MUTED, bg=COLOR_BG,
                                    font=('Segoe UI', 9))
        self.elapsed_lbl.place(x=20, y=554)

        self.filter_info = tk.Checkbutton(self.root, text='Info', bg=COLOR_BG, fg=COLOR_INFO, activebackground=COLOR_BG,
                                          selectcolor=COLOR_BG, font=('Segoe UI', 9), command=self._toggle_info)
        self.filter_info.var = tk.BooleanVar(value=True)
        self.filter_info.config(variable=self.filter_info.var)
        self.filter_info.place(x=650, y=554)

        self.filter_warn = tk.Checkbutton(self.root, text='Warnings', bg=COLOR_BG, fg=COLOR_WARN, activebackground=COLOR_BG,
                                          selectcolor=COLOR_BG, font=('Segoe UI', 9), command=self._toggle_warn)
        self.filter_warn.var = tk.BooleanVar(value=True)
        self.filter_warn.config(variable=self.filter_warn.var)
        self.filter_warn.place(x=710, y=554)

        self.filter_error = tk.Checkbutton(self.root, text='Errors', bg=COLOR_BG, fg=COLOR_ERROR, activebackground=COLOR_BG,
                                           selectcolor=COLOR_BG, font=('Segoe UI', 9), command=self._toggle_error)
        self.filter_error.var = tk.BooleanVar(value=True)
        self.filter_error.config(variable=self.filter_error.var)
        self.filter_error.place(x=780, y=554)

        # Sub-header for current step and ETA
        self.step_lbl = tk.Label(self.root, text='Step 0/0', fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9))
        self.step_lbl.place(x=20, y=116)
        self.substatus_lbl = tk.Label(self.root, text='Preparing…', fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9))
        self.substatus_lbl.place(x=100, y=116)

        # Close button
        self.close_btn = tk.Button(self.root, text='Close', bg=COLOR_ACCENT, fg=COLOR_FG, activebackground=COLOR_ACCENT,
                                   relief='flat', state='disabled', command=self.root.destroy)
        self.close_btn.place(x=804, y=554, width=76, height=24)
        # Stop button (appears on run phase)
        self.stop_btn = tk.Button(self.root, text='Stop', bg=COLOR_BG, fg=COLOR_WARN, activebackground=COLOR_BG,
                                  relief='flat', state='disabled')
        self.stop_btn.place(x=740, y=554, width=60, height=24)
        self._stop_cb = None

        self.root.after(100, self._process_queue)
        self.root.after(120, self._spin)
        self.root.after(500, self._tick_time)

    def enqueue(self, item):
        self.queue.put(item)

    def _append_log(self, level, line):
        if not self._filters.get(level, True):
            return
        self.log_box.configure(state='normal')
        tag = level if level in ('info', 'warn', 'error', 'success') else 'info'
        self.log_box.insert('end', line, tag)
        self.log_box.see('end')
        self.log_box.configure(state='disabled')

    def set_status(self, text):
        self.status_lbl.configure(text=text)

    def set_progress(self, value):
        try:
            self.progress['value'] = max(0, min(100, int(value)))
        except Exception:
            pass

    def animate_progress_to(self, target):
        target = max(0, min(100, int(target)))
        self._anim_target = target
        if self._anim_job is None:
            self._anim_job = self.root.after(15, self._animate_step)

    def _animate_step(self):
        current = int(self.progress['value'])
        if current == self._anim_target:
            self._anim_job = None
            return
        step = 2 if self._anim_target > current else -2
        nxt = current + step
        if (step > 0 and nxt > self._anim_target) or (step < 0 and nxt < self._anim_target):
            nxt = self._anim_target
        self.set_progress(nxt)
        self._anim_job = self.root.after(15, self._animate_step)

    def enable_close(self):
        self.close_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')

    def set_stop_callback(self, cb):
        self._stop_cb = cb
        def _on_click():
            self.stop_btn.configure(state='disabled')
            if self._stop_cb:
                self._stop_cb()
                # Provide immediate UI feedback
                self.enqueue(('status', 'Stopping…'))
        self.stop_btn.configure(command=_on_click)

    def set_stop_enabled(self, enabled: bool):
        self.stop_btn.configure(state='normal' if enabled else 'disabled')

    def _process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if not item:
                    continue
                kind = item[0]
                if kind == 'log':
                    _, level, line = item
                    self._append_log(level, line)
                elif kind == 'status':
                    _, text = item
                    self.set_status(text)
                elif kind == 'progress':
                    _, value = item
                    self.set_progress(value)
                elif kind == 'progress_to':
                    _, value = item
                    self.animate_progress_to(value)
                elif kind == 'enable_close':
                    self.enable_close()
                elif kind == 'step_hdr':
                    _, idx, total, name = item
                    self.step_lbl.configure(text=f"Step {idx}/{total}")
                    self.substatus_lbl.configure(text=name)
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)

    def _spin(self):
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
        self.spinner_lbl.configure(text=self._spinner_frames[self._spinner_index])
        self.root.after(120, self._spin)

    def _tick_time(self):
        elapsed = max(0, int(time.time() - self._start_time))
        mm, ss = divmod(elapsed, 60)
        hh, mm = divmod(mm, 60)
        self.elapsed_lbl.configure(text=f"Elapsed: {hh:02d}:{mm:02d}:{ss:02d} • ETA: {self._last_eta}")
        self.root.after(500, self._tick_time)

    def set_eta(self, seconds_remaining):
        if seconds_remaining is None or seconds_remaining <= 0:
            self._last_eta = '—'
        else:
            s = int(seconds_remaining)
            mm, ss = divmod(s, 60)
            hh, mm = divmod(mm, 60)
            self._last_eta = f"{hh:02d}:{mm:02d}:{ss:02d}"

    # Filter toggles
    def _toggle_info(self):
        self._filters['info'] = bool(self.filter_info.var.get())

    def _toggle_warn(self):
        self._filters['warn'] = bool(self.filter_warn.var.get())

    def _toggle_error(self):
        self._filters['error'] = bool(self.filter_error.var.get())

    def run(self):
        self.root.mainloop()

    # Component selection dialog (modular, scalable)
    def show_selection(self, registry, on_start, preselected_ids=None):
        dlg = tk.Toplevel(self.root)
        dlg.title('Select Components')
        dlg.configure(bg=COLOR_BG)
        dlg.geometry('720x540')
        dlg.transient(self.root)
        dlg.grab_set()

        title = tk.Label(dlg, text='Choose what to install', fg=COLOR_FG, bg=COLOR_BG, font=('Segoe UI', 12, 'bold'))
        title.pack(anchor='w', padx=16, pady=(16,4))
        subtitle = tk.Label(dlg, text='You can add more tools later. This selection is modular and grouped by purpose.', fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9))
        subtitle.pack(anchor='w', padx=16, pady=(0,8))

        container = tk.Frame(dlg, bg=COLOR_BG)
        container.pack(fill='both', expand=True, padx=12, pady=8)

        # Scrollable area for many items
        canvas = tk.Canvas(container, bg=COLOR_BG, highlightthickness=0)
        vsb = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
        frame = tk.Frame(canvas, bg=COLOR_BG)
        frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0,0), window=frame, anchor='nw')
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        vars_map = {}
        for cat in registry:
            cat_lbl = tk.Label(frame, text=cat['name'], fg=COLOR_FG, bg=COLOR_BG, font=('Segoe UI', 10, 'bold'))
            cat_lbl.pack(anchor='w', padx=8, pady=(12,4))
            if cat.get('description'):
                desc = tk.Label(frame, text=cat['description'], fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9))
                desc.pack(anchor='w', padx=16, pady=(0,6))
            for item in cat['items']:
                var = tk.BooleanVar(value=(preselected_ids is None and item.get('default', True)) or (preselected_ids and item['id'] in preselected_ids))
                vars_map[item['id']] = var
                row = tk.Frame(frame, bg=COLOR_BG)
                row.pack(fill='x', padx=16, pady=2)
                cb = tk.Checkbutton(row, text=item['name'], bg=COLOR_BG, fg=COLOR_FG, variable=var,
                                    activebackground=COLOR_BG, selectcolor=COLOR_BG, font=('Segoe UI', 10))
                cb.pack(side='left')
                if item.get('description'):
                    meta = tk.Label(row, text=item['description'], fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9))
                    meta.pack(side='left', padx=10)

        btns = tk.Frame(dlg, bg=COLOR_BG)
        btns.pack(fill='x', padx=16, pady=8)

        def select_all():
            for v in vars_map.values():
                v.set(True)
        def deselect_all():
            for v in vars_map.values():
                v.set(False)
        tk.Button(btns, text='Select All', command=select_all, bg=COLOR_BG, fg=COLOR_INFO, relief='flat').pack(side='left')
        tk.Button(btns, text='Deselect All', command=deselect_all, bg=COLOR_BG, fg=COLOR_WARN, relief='flat').pack(side='left', padx=8)

        def start():
            selected = [k for k,v in vars_map.items() if v.get()]
            dlg.destroy()
            on_start(selected)
        def cancel():
            dlg.destroy()
            self.root.destroy()
        tk.Button(btns, text='Start Install', command=start, bg=COLOR_ACCENT, fg=COLOR_FG, relief='flat').pack(side='right')
        tk.Button(btns, text='Cancel', command=cancel, bg=COLOR_BG, fg=COLOR_MUTED, relief='flat').pack(side='right', padx=8)

# Helpers

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_ps(ps_code: str, cwd: str = REPO_DIR, timeout: int = None):
    # Force strict error behavior inside PowerShell block
    cmd = [
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-Command', f"$ErrorActionPreference='Stop'; {ps_code}"
    ]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def import_common_and(ps_inner: str) -> str:
    # Properly quote module path
    mod = MODULE_PATH.replace('`', '``').replace("'", "''")
    return f"Import-Module '{mod}' -Force -DisableNameChecking; {ps_inner}"


def dot_source_and(ps1_path: str, call: str) -> str:
    p = ps1_path.replace('`', '``').replace("'", "''")
    return f". '{p}'; {call}"


def ensure_choco(logger: Logger):
    logger.info('Ensuring Chocolatey...')
    code = import_common_and('Ensure-Chocolatey')
    res = run_ps(code)
    if res.returncode != 0:
        logger.warn(f"Chocolatey setup returned {res.returncode}: {res.stderr.strip()}")
    else:
        logger.success('Chocolatey is ready.')


def install_choco_pkg(name: str, force: bool, logger: Logger, what_if: bool=False):
    args = f"-Name '{name}'"
    if force:
        args += ' -ForceReinstall'
    if what_if:
        args += ' -WhatIf'
    code = import_common_and(f"Install-ChocoPackage {args} | Out-Null")
    res = run_ps(code)
    if res.returncode != 0:
        logger.warn(f"{name} install returned {res.returncode}: {res.stderr.strip()}")
    else:
        logger.success(f"{name} installed (or already present).")


def run_installer_ps(script_name: str, func: str, logger: Logger, args: str = '', what_if: bool=False):
    ps1 = os.path.join(UTIL_DIR, script_name)
    if what_if and '-WhatIf' not in args:
        args = (args + ' -WhatIf').strip()
    code = dot_source_and(ps1, f"{func} {args}")
    res = run_ps(code)
    if res.returncode != 0:
        logger.warn(f"{func} returned {res.returncode}: {res.stderr.strip()}")
    else:
        logger.success(f"{func} completed.")


def call_common(func: str, args: str, logger: Logger):
    code = import_common_and(f"{func} {args}")
    res = run_ps(code)
    if res.returncode != 0:
        logger.warn(f"{func} returned {res.returncode}: {res.stderr.strip()}")
    else:
        logger.success(f"{func} completed.")


def copy_wallpaper(logger: Logger):
    src = os.path.join(ASSETS_DIR, 'wallpaper.jpg')
    if not os.path.exists(src):
        logger.warn('Wallpaper not found in assets; skipping.')
        return None
    dest_dir = r'C:\\Tools\\Wallpapers'
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, 'holmes-wallpaper.jpg')
    try:
        import shutil
        shutil.copyfile(src, dest)
        logger.success(f'Wallpaper copied to {dest}')
        return dest
    except Exception as e:
        logger.warn(f'Failed to copy wallpaper: {e}')
        return None


def net_check(logger: Logger) -> bool:
    import urllib.request
    ok = 0
    for url in ('https://www.google.com/generate_204', 'https://github.com'):
        try:
            with urllib.request.urlopen(url, timeout=7) as resp:  # nosec B310
                if 200 <= resp.status < 400:
                    ok += 1
                    logger.success(f'Reachable: {url}')
                else:
                    logger.warn(f'Unexpected status {resp.status} for {url}')
        except Exception as e:
            logger.warn(f'Not reachable: {url} ({e})')
    logger.info(f'Network connectivity summary: {ok}/2 reachable')
    return ok > 0


def build_steps(args, logger: Logger):
    steps = []

    # 1. Admin + OS check
    steps.append(('Assert Windows/Admin', lambda: (
        (_ for _ in ()).throw(RuntimeError('Windows-only setup')) if sys.platform != 'win32' else None,
        (_ for _ in ()).throw(RuntimeError('Run as Administrator')) if not is_admin() else None
    )))

    # 2. Network
    if not args.skip_network_check:
        steps.append(('Network connectivity', lambda: net_check(logger)))
    else:
        logger.warn('Skipping network connectivity check.')

    # 3. Chocolatey
    steps.append(('Ensure Chocolatey', lambda: ensure_choco(logger)))

    # 4. Python core tools (we are running in Python already; just ensure pip updated)
    steps.append(('Upgrade pip/setuptools/wheel', lambda: _upgrade_pip(logger)))

    # 5. Wireshark
    if not args.skip_wireshark:
        steps.append(('Install Wireshark', lambda: install_choco_pkg('wireshark', args.force_reinstall, logger, args.what_if)))
    else:
        logger.info('Skipping Wireshark.')

    # 6. .NET Desktop
    if not args.skip_dotnet_desktop:
        steps.append(('Install .NET 6 Desktop', lambda: install_choco_pkg('dotnet-6.0-desktopruntime', args.force_reinstall, logger, args.what_if)))
    else:
        logger.info('Skipping .NET Desktop Runtime.')

    # 7. DnSpyEx
    if not args.skip_dnspyex:
        steps.append(('Install DnSpyEx', lambda: install_choco_pkg('dnspyex', args.force_reinstall, logger, args.what_if)))
    else:
        logger.info('Skipping DnSpyEx.')

    # 8. PeStudio
    if not args.skip_pestudio:
        steps.append(('Install PeStudio', lambda: install_choco_pkg('pestudio', args.force_reinstall, logger, args.what_if)))
    else:
        logger.info('Skipping PeStudio.')

    # 9. VS Code
    if not args.skip_vscode:
        steps.append(('Install VS Code', lambda: install_choco_pkg('vscode', args.force_reinstall, logger, args.what_if)))
        steps.append(('Pin VS Code', lambda: call_common('Pin-TaskbarItem', r"-Path 'C:\\Program Files\\Microsoft VS Code\\Code.exe'", logger)))
    else:
        logger.info('Skipping VS Code.')

    # 10. SQLite Browser
    if not args.skip_sqlitebrowser:
        steps.append(('Install DB Browser for SQLite', lambda: install_choco_pkg('sqlitebrowser', args.force_reinstall, logger, args.what_if)))
        steps.append(('Pin DB Browser', lambda: _pin_db_browser(logger)))
    else:
        logger.info('Skipping DB Browser for SQLite.')

    # 11. EZ Tools
    if not args.skip_eztools:
        steps.append(('Install EZ Tools', lambda: run_installer_ps('install-eztools.ps1', 'Install-EZTools', logger, args=(f"-LogDir '{LOG_DIR_DEFAULT}'"), what_if=args.what_if)))
        steps.append(('Pin MFTExplorer', lambda: call_common('Pin-TaskbarItem', r"-Path 'C:\\Tools\\EricZimmermanTools\\net6\\MFTExplorer.exe'", logger)))
    else:
        logger.info('Skipping EZ Tools.')

    # 12. RegRipper
    if not args.skip_regripper:
        steps.append(('Install RegRipper', lambda: run_installer_ps('install-regripper.ps1', 'Install-RegRipper', logger, what_if=args.what_if)))
    else:
        logger.info('Skipping RegRipper.')

    # 13. Chainsaw
    if not args.skip_chainsaw:
        steps.append(('Install Chainsaw', lambda: run_installer_ps('install-chainsaw.ps1', 'Install-Chainsaw', logger, what_if=args.what_if)))
    else:
        logger.info('Skipping Chainsaw.')

    # 14. Wallpaper
    if not args.skip_wallpaper:
        steps.append(('Copy wallpaper', lambda: copy_wallpaper(logger)))
        steps.append(('Apply wallpaper', lambda: _apply_wallpaper(logger)))
    else:
        logger.info('Skipping wallpaper setup.')

    # 15. Windows appearance
    steps.append(('Apply Windows appearance', lambda: call_common('Set-WindowsAppearance', "-DarkMode -AccentHex '#0078D7' -ShowAccentOnTaskbar", logger)))

    return steps


def build_registry():
    # Modular registry of installable components (grouped)
    return [
        {
            'name': 'Core',
            'description': 'Essential checks and helpers for a successful setup.',
            'items': [
                { 'id': 'network', 'name': 'Network connectivity check', 'description': 'Verify internet access before downloads', 'default': True },
                { 'id': 'choco', 'name': 'Chocolatey', 'description': 'Windows package manager', 'default': True },
                { 'id': 'pip', 'name': 'Upgrade pip & tools', 'description': 'pip, setuptools, wheel, pipx, virtualenv', 'default': True },
            ]
        },
        {
            'name': 'Applications',
            'description': 'Analysis tools and utilities.',
            'items': [
                { 'id': 'wireshark', 'name': 'Wireshark', 'default': True },
                { 'id': 'dotnet', 'name': '.NET 6 Desktop Runtime', 'default': True },
                { 'id': 'dnspyex', 'name': 'DnSpyEx', 'default': True },
                { 'id': 'pestudio', 'name': 'PeStudio', 'default': True },
                { 'id': 'vscode', 'name': 'Visual Studio Code', 'default': True },
                { 'id': 'sqlitebrowser', 'name': 'DB Browser for SQLite', 'default': True },
            ]
        },
        {
            'name': 'Forensics Bundles',
            'description': 'Specialized forensic tooling.',
            'items': [
                { 'id': 'eztools', 'name': 'Eric Zimmerman Tools (EZ Tools)', 'default': True },
                { 'id': 'regripper', 'name': 'RegRipper', 'default': True },
                { 'id': 'chainsaw', 'name': 'Chainsaw', 'default': True },
            ]
        },
        {
            'name': 'Personalization',
            'description': 'Make the VM look and feel great.',
            'items': [
                { 'id': 'wallpaper', 'name': 'Holmes wallpaper', 'default': True },
                { 'id': 'appearance', 'name': 'Windows appearance tweaks', 'default': True },
            ]
        }
    ]


def build_steps_from_selection(selected_ids, args, logger: Logger):
    steps = []
    # Always assert platform/admin
    steps.append(('Assert Windows/Admin', lambda: (
        (_ for _ in ()).throw(RuntimeError('Windows-only setup')) if sys.platform != 'win32' else None,
        (_ for _ in ()).throw(RuntimeError('Run as Administrator')) if not is_admin() else None
    )))

    if 'network' in selected_ids:
        steps.append(('Network connectivity', lambda: net_check(logger)))
    else:
        logger.warn('Skipping network connectivity check.')

    if 'choco' in selected_ids:
        steps.append(('Ensure Chocolatey', lambda: ensure_choco(logger)))
    if 'pip' in selected_ids:
        steps.append(('Upgrade pip/setuptools/wheel', lambda: _upgrade_pip(logger)))

    if 'wireshark' in selected_ids:
        steps.append(('Install Wireshark', lambda: install_choco_pkg('wireshark', args.force_reinstall, logger, args.what_if)))
    if 'dotnet' in selected_ids:
        steps.append(('Install .NET 6 Desktop', lambda: install_choco_pkg('dotnet-6.0-desktopruntime', args.force_reinstall, logger, args.what_if)))
    if 'dnspyex' in selected_ids:
        steps.append(('Install DnSpyEx', lambda: install_choco_pkg('dnspyex', args.force_reinstall, logger, args.what_if)))
    if 'pestudio' in selected_ids:
        steps.append(('Install PeStudio', lambda: install_choco_pkg('pestudio', args.force_reinstall, logger, args.what_if)))
    if 'vscode' in selected_ids:
        steps.append(('Install VS Code', lambda: install_choco_pkg('vscode', args.force_reinstall, logger, args.what_if)))
        steps.append(('Pin VS Code', lambda: call_common('Pin-TaskbarItem', r"-Path 'C:\\Program Files\\Microsoft VS Code\\Code.exe'", logger)))
    if 'sqlitebrowser' in selected_ids:
        steps.append(('Install DB Browser for SQLite', lambda: install_choco_pkg('sqlitebrowser', args.force_reinstall, logger, args.what_if)))
        steps.append(('Pin DB Browser', lambda: _pin_db_browser(logger)))

    if 'eztools' in selected_ids:
        steps.append(('Install EZ Tools', lambda: run_installer_ps('install-eztools.ps1', 'Install-EZTools', logger, args=(f"-LogDir '{LOG_DIR_DEFAULT}'"), what_if=args.what_if)))
        steps.append(('Pin MFTExplorer', lambda: call_common('Pin-TaskbarItem', r"-Path 'C:\\Tools\\EricZimmermanTools\\net6\\MFTExplorer.exe'", logger)))
    if 'regripper' in selected_ids:
        steps.append(('Install RegRipper', lambda: run_installer_ps('install-regripper.ps1', 'Install-RegRipper', logger, what_if=args.what_if)))
    if 'chainsaw' in selected_ids:
        steps.append(('Install Chainsaw', lambda: run_installer_ps('install-chainsaw.ps1', 'Install-Chainsaw', logger, what_if=args.what_if)))

    if 'wallpaper' in selected_ids:
        steps.append(('Copy wallpaper', lambda: copy_wallpaper(logger)))
        steps.append(('Apply wallpaper', lambda: _apply_wallpaper(logger)))
    if 'appearance' in selected_ids:
        steps.append(('Apply Windows appearance', lambda: call_common('Set-WindowsAppearance', "-DarkMode -AccentHex '#0078D7' -ShowAccentOnTaskbar", logger)))

    return steps


def _upgrade_pip(logger: Logger):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'pip', 'setuptools', 'wheel'], check=False, capture_output=True, text=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'pipx', 'virtualenv'], check=False, capture_output=True, text=True)
        logger.success('Pip and core tools upgraded.')
    except Exception as e:
        logger.warn(f'pip upgrade failed: {e}')


def _pin_db_browser(logger: Logger):
    # Try x64 then x86 path
    paths = [
        r"C:\\Program Files\\DB Browser for SQLite\\DB Browser for SQLite.exe",
        r"C:\\Program Files (x86)\\DB Browser for SQLite\\DB Browser for SQLite.exe",
    ]
    for p in paths:
        res = run_ps(import_common_and(f"Pin-TaskbarItem -Path '{p}'"))
        if res.returncode == 0:
            logger.success('DB Browser pinned (or already pinned).')
            return
    logger.warn('DB Browser executable not found to pin.')


def _apply_wallpaper(logger: Logger):
    # Use common function to set wallpaper if possible
    dest = os.path.join(r'C:\\Tools\\Wallpapers', 'holmes-wallpaper.jpg')
    if not os.path.exists(dest):
        logger.warn('Wallpaper file missing; skipping apply.')
        return
    res = run_ps(import_common_and(f"Set-Wallpaper -ImagePath '{dest}' -Style Fill"))
    if res.returncode != 0:
        logger.warn(f'Apply wallpaper returned {res.returncode}: {res.stderr.strip()}')
    else:
        logger.success('Wallpaper applied.')


def run_steps(steps, ui: UI, logger: Logger, cancel_event=None):
    total = len(steps)
    start = time.time()
    for i, (name, action) in enumerate(steps, start=1):
        if cancel_event and cancel_event.is_set():
            logger.warn('Cancelled by user before next step.')
            break
        ui.enqueue(('step_hdr', i, total, name))
        ui.enqueue(('status', f"Working"))
        ui.enqueue(('progress_to', int((i-1)*100/total)))
        logger.current_step = name
        logger.info(f"{name}…")
        t0 = time.time()
        try:
            action()
            logger.success(f"{name} completed.")
        except Exception as e:
            logger.error(f"{name} failed: {e}")
        t1 = time.time()
        done_fraction = i / max(1, total)
        elapsed = t1 - start
        eta = (elapsed / done_fraction) - elapsed if done_fraction > 0 else None
        ui.set_eta(eta)
        ui.enqueue(('progress_to', int(i*100/total)))
    logger.current_step = None


def run_steps_console(steps, logger: Logger):
    total = len(steps)
    for i, (name, action) in enumerate(steps, start=1):
        logger.current_step = name
        logger.info(f"[{i}/{total}] {name}…")
        try:
            action()
            logger.success(f"{name} completed.")
        except Exception as e:
            logger.error(f"{name} failed: {e}")
    logger.current_step = None


def main():
    parser = argparse.ArgumentParser(description='Holmes VM Setup (Python UI)')
    parser.add_argument('--no-gui', action='store_true')
    parser.add_argument('--what-if', action='store_true')
    parser.add_argument('--force-reinstall', action='store_true')
    parser.add_argument('--log-dir', default=LOG_DIR_DEFAULT)
    # skip flags
    parser.add_argument('--skip-wireshark', action='store_true')
    parser.add_argument('--skip-dotnet-desktop', action='store_true')
    parser.add_argument('--skip-dnspyex', action='store_true')
    parser.add_argument('--skip-pestudio', action='store_true')
    parser.add_argument('--skip-eztools', action='store_true')
    parser.add_argument('--skip-regripper', action='store_true')
    parser.add_argument('--skip-wallpaper', action='store_true')
    parser.add_argument('--skip-network-check', action='store_true')
    parser.add_argument('--skip-chainsaw', action='store_true')
    parser.add_argument('--skip-vscode', action='store_true')
    parser.add_argument('--skip-sqlitebrowser', action='store_true')

    args = parser.parse_args()

    os.makedirs(args.log_dir, exist_ok=True)
    log_file = os.path.join(args.log_dir, f"HolmesVM-setup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")
    ui = None

    # Decide GUI availability
    use_gui = (not args.no_gui) and (tk is not None) and (ttk is not None) and (scrolledtext is not None)
    if use_gui:
        try:
            ui = UI(APP_NAME)
        except Exception:
            use_gui = False
            ui = None

    logger = Logger(log_file, ui)

    if use_gui and ui is not None:
        # GUI mode: show selection first then run
        cancel_event = threading.Event()
        ui.set_stop_callback(cancel_event.set)

        registry = build_registry()

        def on_start(selected_ids):
            steps = build_steps_from_selection(selected_ids, args, logger)
            ui.set_stop_enabled(True)
            def _runner():
                try:
                    run_steps(steps, ui, logger, cancel_event)
                finally:
                    ui.enqueue(('enable_close', None))
            t = threading.Thread(target=_runner, daemon=True)
            t.start()

        # Show selection dialog and enter UI loop
        ui.show_selection(registry, on_start)
        ui.run()
    else:
        logger.warn('GUI not available; running in console mode.')
        steps = build_steps(args, logger)
        run_steps_console(steps, logger)

    logger.success('Setup finished.')


if __name__ == '__main__':
    main()

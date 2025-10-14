#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main UI window for Holmes VM setup
"""

import queue
import time
from typing import List, Dict, Any, Callable, Optional

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import scrolledtext
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False
    tk = None
    ttk = None
    scrolledtext = None

from .colors import *


class UI:
    """Main UI window for Holmes VM setup"""
    
    def __init__(self, title: str):
        if not TK_AVAILABLE:
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
        self._filters = {'info': True, 'warn': True, 'error': True, 'success': True}
        
        self._setup_ui()
        self._start_background_tasks()

    def _setup_ui(self):
        """Setup all UI components"""
        # Title
        self.title_lbl = tk.Label(
            self.root, text='Setting up Holmes VM',
            fg=COLOR_FG, bg=COLOR_BG, font=('Segoe UI', 14, 'bold')
        )
        self.title_lbl.place(x=20, y=18)

        # Status
        self.status_lbl = tk.Label(
            self.root, text='Initializing',
            fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 10)
        )
        self.status_lbl.place(x=20, y=54)

        # Spinner
        self._spinner_frames = list('⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏')
        self._spinner_index = 0
        self.spinner_lbl = tk.Label(
            self.root, text=self._spinner_frames[0],
            fg=COLOR_ACCENT, bg=COLOR_BG, font=('Segoe UI', 12, 'bold')
        )
        self.spinner_lbl.place(x=860, y=18)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.root, orient='horizontal', length=820, mode='determinate'
        )
        self.progress.place(x=20, y=80)
        
        try:
            style = ttk.Style()
            style.theme_use('default')
            style.configure('TProgressbar', troughcolor=COLOR_BG, background=COLOR_ACCENT, thickness=12)
        except Exception:
            pass

        # Log box
        self.log_box = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state='disabled',
            bg=COLOR_BG, fg=COLOR_FG, font=('Consolas', 10)
        )
        self.log_box.place(x=20, y=146, width=860, height=400)
        
        # Tags for colors
        self.log_box.tag_config('info', foreground=COLOR_INFO)
        self.log_box.tag_config('warn', foreground=COLOR_WARN)
        self.log_box.tag_config('error', foreground=COLOR_ERROR)
        self.log_box.tag_config('success', foreground=COLOR_SUCCESS)

        # Footer: elapsed / ETA
        self.elapsed_lbl = tk.Label(
            self.root, text='Elapsed: 00:00 • ETA: —',
            fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9)
        )
        self.elapsed_lbl.place(x=20, y=554)

        # Filter checkboxes
        self._create_filter_checkboxes()

        # Sub-header for current step
        self.step_lbl = tk.Label(
            self.root, text='Step 0/0',
            fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9)
        )
        self.step_lbl.place(x=20, y=116)
        
        self.substatus_lbl = tk.Label(
            self.root, text='Preparing…',
            fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9)
        )
        self.substatus_lbl.place(x=100, y=116)

        # Buttons
        self.close_btn = tk.Button(
            self.root, text='Close', bg=COLOR_ACCENT, fg=COLOR_FG,
            activebackground=COLOR_ACCENT, relief='flat', state='disabled',
            command=self.root.destroy
        )
        self.close_btn.place(x=804, y=554, width=76, height=24)
        
        self.stop_btn = tk.Button(
            self.root, text='Stop', bg=COLOR_BG, fg=COLOR_WARN,
            activebackground=COLOR_BG, relief='flat', state='disabled'
        )
        self.stop_btn.place(x=740, y=554, width=60, height=24)
        self._stop_cb = None

    def _create_filter_checkboxes(self):
        """Create log filter checkboxes"""
        self.filter_info = tk.Checkbutton(
            self.root, text='Info', bg=COLOR_BG, fg=COLOR_INFO,
            activebackground=COLOR_BG, selectcolor=COLOR_BG,
            font=('Segoe UI', 9), command=self._toggle_info
        )
        self.filter_info.var = tk.BooleanVar(value=True)
        self.filter_info.config(variable=self.filter_info.var)
        self.filter_info.place(x=650, y=554)

        self.filter_warn = tk.Checkbutton(
            self.root, text='Warnings', bg=COLOR_BG, fg=COLOR_WARN,
            activebackground=COLOR_BG, selectcolor=COLOR_BG,
            font=('Segoe UI', 9), command=self._toggle_warn
        )
        self.filter_warn.var = tk.BooleanVar(value=True)
        self.filter_warn.config(variable=self.filter_warn.var)
        self.filter_warn.place(x=710, y=554)

        self.filter_error = tk.Checkbutton(
            self.root, text='Errors', bg=COLOR_BG, fg=COLOR_ERROR,
            activebackground=COLOR_BG, selectcolor=COLOR_BG,
            font=('Segoe UI', 9), command=self._toggle_error
        )
        self.filter_error.var = tk.BooleanVar(value=True)
        self.filter_error.config(variable=self.filter_error.var)
        self.filter_error.place(x=780, y=554)

    def _start_background_tasks(self):
        """Start background update tasks"""
        self.root.after(100, self._process_queue)
        self.root.after(120, self._spin)
        self.root.after(500, self._tick_time)

    def enqueue(self, item: tuple):
        """Add item to processing queue"""
        self.queue.put(item)

    def _append_log(self, level: str, line: str):
        """Append log message to log box"""
        if not self._filters.get(level, True):
            return
            
        self.log_box.configure(state='normal')
        tag = level if level in ('info', 'warn', 'error', 'success') else 'info'
        self.log_box.insert('end', line, tag)
        self.log_box.see('end')
        self.log_box.configure(state='disabled')

    def set_status(self, text: str):
        """Update status label"""
        self.status_lbl.configure(text=text)

    def set_progress(self, value: int):
        """Set progress bar value"""
        try:
            self.progress['value'] = max(0, min(100, int(value)))
        except Exception:
            pass

    def animate_progress_to(self, target: int):
        """Animate progress bar to target value"""
        target = max(0, min(100, int(target)))
        self._anim_target = target
        if self._anim_job is None:
            self._anim_job = self.root.after(15, self._animate_step)

    def _animate_step(self):
        """Single step of progress animation"""
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
        """Enable close button"""
        self.close_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')

    def set_stop_callback(self, cb: Callable):
        """Set callback for stop button"""
        self._stop_cb = cb
        def _on_click():
            self.stop_btn.configure(state='disabled')
            if self._stop_cb:
                self._stop_cb()
                self.enqueue(('status', 'Stopping…'))
        self.stop_btn.configure(command=_on_click)

    def set_stop_enabled(self, enabled: bool):
        """Enable/disable stop button"""
        self.stop_btn.configure(state='normal' if enabled else 'disabled')

    def _process_queue(self):
        """Process items from queue"""
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
        """Update spinner animation"""
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
        self.spinner_lbl.configure(text=self._spinner_frames[self._spinner_index])
        self.root.after(120, self._spin)

    def _tick_time(self):
        """Update elapsed time display"""
        elapsed = max(0, int(time.time() - self._start_time))
        mm, ss = divmod(elapsed, 60)
        hh, mm = divmod(mm, 60)
        self.elapsed_lbl.configure(text=f"Elapsed: {hh:02d}:{mm:02d}:{ss:02d} • ETA: {self._last_eta}")
        self.root.after(500, self._tick_time)

    def set_eta(self, seconds_remaining: Optional[float]):
        """Set estimated time remaining"""
        if seconds_remaining is None or seconds_remaining <= 0:
            self._last_eta = '—'
        else:
            s = int(seconds_remaining)
            mm, ss = divmod(s, 60)
            hh, mm = divmod(mm, 60)
            self._last_eta = f"{hh:02d}:{mm:02d}:{ss:02d}"

    def _toggle_info(self):
        """Toggle info log filter"""
        self._filters['info'] = bool(self.filter_info.var.get())

    def _toggle_warn(self):
        """Toggle warning log filter"""
        self._filters['warn'] = bool(self.filter_warn.var.get())

    def _toggle_error(self):
        """Toggle error log filter"""
        self._filters['error'] = bool(self.filter_error.var.get())

    def run(self):
        """Start UI main loop"""
        self.root.mainloop()

    def show_selection(self, registry: List[Dict[str, Any]], on_start: Callable, preselected_ids: Optional[List[str]] = None):
        """Show component selection dialog"""
        dlg = tk.Toplevel(self.root)
        dlg.title('Select Components')
        dlg.configure(bg=COLOR_BG)
        dlg.geometry('720x540')
        dlg.transient(self.root)
        dlg.grab_set()

        # Title and subtitle
        title = tk.Label(
            dlg, text='Choose what to install',
            fg=COLOR_FG, bg=COLOR_BG, font=('Segoe UI', 12, 'bold')
        )
        title.pack(anchor='w', padx=16, pady=(16, 4))
        
        subtitle = tk.Label(
            dlg, text='You can add more tools later. This selection is modular and grouped by purpose.',
            fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9)
        )
        subtitle.pack(anchor='w', padx=16, pady=(0, 8))

        # Scrollable container
        container = tk.Frame(dlg, bg=COLOR_BG)
        container.pack(fill='both', expand=True, padx=12, pady=8)

        canvas = tk.Canvas(container, bg=COLOR_BG, highlightthickness=0)
        vsb = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
        frame = tk.Frame(canvas, bg=COLOR_BG)
        
        frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=frame, anchor='nw')
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        # Build selection UI
        vars_map = {}
        for cat in registry:
            cat_lbl = tk.Label(
                frame, text=cat['name'],
                fg=COLOR_FG, bg=COLOR_BG, font=('Segoe UI', 10, 'bold')
            )
            cat_lbl.pack(anchor='w', padx=8, pady=(12, 4))
            
            if cat.get('description'):
                desc = tk.Label(
                    frame, text=cat['description'],
                    fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9)
                )
                desc.pack(anchor='w', padx=16, pady=(0, 6))
                
            for item in cat['items']:
                default_selected = (
                    preselected_ids is None and item.get('default', True)
                ) or (
                    preselected_ids and item['id'] in preselected_ids
                )
                var = tk.BooleanVar(value=default_selected)
                vars_map[item['id']] = var
                
                row = tk.Frame(frame, bg=COLOR_BG)
                row.pack(fill='x', padx=16, pady=2)
                
                cb = tk.Checkbutton(
                    row, text=item['name'], bg=COLOR_BG, fg=COLOR_FG,
                    variable=var, activebackground=COLOR_BG,
                    selectcolor=COLOR_BG, font=('Segoe UI', 10)
                )
                cb.pack(side='left')
                
                if item.get('description'):
                    meta = tk.Label(
                        row, text=item['description'],
                        fg=COLOR_MUTED, bg=COLOR_BG, font=('Segoe UI', 9)
                    )
                    meta.pack(side='left', padx=10)

        # Buttons
        btns = tk.Frame(dlg, bg=COLOR_BG)
        btns.pack(fill='x', padx=16, pady=8)

        def select_all():
            for v in vars_map.values():
                v.set(True)
                
        def deselect_all():
            for v in vars_map.values():
                v.set(False)
                
        tk.Button(
            btns, text='Select All', command=select_all,
            bg=COLOR_BG, fg=COLOR_INFO, relief='flat'
        ).pack(side='left')
        
        tk.Button(
            btns, text='Deselect All', command=deselect_all,
            bg=COLOR_BG, fg=COLOR_WARN, relief='flat'
        ).pack(side='left', padx=8)

        def start():
            selected = [k for k, v in vars_map.items() if v.get()]
            dlg.destroy()
            on_start(selected)
            
        def cancel():
            dlg.destroy()
            self.root.destroy()
            
        tk.Button(
            btns, text='Start Install', command=start,
            bg=COLOR_ACCENT, fg=COLOR_FG, relief='flat'
        ).pack(side='right')
        
        tk.Button(
            btns, text='Cancel', command=cancel,
            bg=COLOR_BG, fg=COLOR_MUTED, relief='flat'
        ).pack(side='right', padx=8)


def is_tk_available() -> bool:
    """Check if Tkinter is available"""
    return TK_AVAILABLE

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main UI window for Holmes VM setup
Enhanced with Sherlock Holmes mystery theme, smooth animations, and modern design
"""

import queue
import time
from typing import List, Dict, Any, Callable, Optional

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import scrolledtext, font
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False
    tk = None
    ttk = None
    scrolledtext = None

from .colors import *


# Sherlock Holmes themed banner for GUI
HOLMES_ASCII_SMALL = """
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║   🔍 SHERLOCK HOLMES • DIGITAL FORENSICS VM SETUP                                                     ║
║      "Elementary, my dear Watson" • The Game is Afoot                                                 ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

class UI:
    """Main UI window for Holmes VM setup with enhanced Sherlock Holmes theme

    Enhancements added:
    - Animated progress easing
    - Step timeline panel with per-step success/failure icons
    - Smooth fade-in for log lines (simulated via color cycling)
    - Toast notifications for completion and errors
    - Better button hover and disabled state styling
    """
    
    def __init__(self, title: str):
        if not TK_AVAILABLE:
            raise RuntimeError('Tkinter not available; run in console mode')
            
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry('1000x700')
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(True, True)
        
        # Attempt to set minimum size
        try:
            self.root.minsize(900, 650)
        except Exception:
            pass
        
        try:
            self.root.iconbitmap(False)
        except Exception:
            pass

        self.queue = queue.Queue()
        self._anim_target = 0
        self._anim_job = None
        self._start_time = time.time()
        self._last_eta = '—'
        self._filters = {'info': True, 'warn': True, 'error': True, 'success': True, 'verbose': False}
        self._log_line_count = 0
        self._max_log_lines = 1000  # Limit log lines for performance
        self._timeline_steps = []
        self._toast_windows = []

        # Custom fonts
        self._setup_fonts()
        
        self._setup_ui()
        self._start_background_tasks()

    def _setup_fonts(self):
        """Setup custom fonts for better typography"""
        try:
            self.title_font = font.Font(family='Segoe UI', size=13, weight='bold')
            self.header_font = font.Font(family='Segoe UI', size=10, weight='bold')
            self.body_font = font.Font(family='Segoe UI', size=9)
            self.small_font = font.Font(family='Segoe UI', size=8)
            self.mono_font = font.Font(family='Consolas', size=9)
        except Exception:
            # Fallback to default fonts
            self.title_font = ('Arial', 13, 'bold')
            self.header_font = ('Arial', 10, 'bold')
            self.body_font = ('Arial', 9)
            self.small_font = ('Arial', 8)
            self.mono_font = ('Courier', 9)

    def _setup_ui(self):
        """Setup all UI components with enhanced styling"""
        
        # === Header Section with Banner ===
        header_frame = tk.Frame(self.root, bg=COLOR_BG_SECONDARY, height=100)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title with magnifying glass icon
        self.title_lbl = tk.Label(
            header_frame, text='🔍 HOLMES VM SETUP',
            fg=COLOR_ACCENT_LIGHT, bg=COLOR_BG_SECONDARY, 
            font=self.title_font
        )
        self.title_lbl.pack(pady=(15, 5))
        
        # Subtitle
        subtitle_lbl = tk.Label(
            header_frame, text='Digital Forensics Environment • "Elementary, my dear Watson"',
            fg=COLOR_MUTED, bg=COLOR_BG_SECONDARY, font=self.small_font
        )
        subtitle_lbl.pack()
        
        # Status line
        self.status_lbl = tk.Label(
            header_frame, text='Initializing investigation...',
            fg=COLOR_INFO, bg=COLOR_BG_SECONDARY, font=self.body_font
        )
        self.status_lbl.pack(pady=(8, 5))

        # === Progress Section ===
        progress_frame = tk.Frame(self.root, bg=COLOR_BG, height=120)
        progress_frame.pack(fill='x', padx=25, pady=(15, 0))
        progress_frame.pack_propagate(False)
        
        # Step indicator
        step_info_frame = tk.Frame(progress_frame, bg=COLOR_BG)
        step_info_frame.pack(fill='x', pady=(0, 8))
        
        self.step_lbl = tk.Label(
            step_info_frame, text='Step 0/0',
            fg=COLOR_ACCENT, bg=COLOR_BG, font=self.header_font
        )
        self.step_lbl.pack(side='left')
        
        # Spinner next to step
        self._spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self._spinner_index = 0
        self.spinner_lbl = tk.Label(
            step_info_frame, text=self._spinner_frames[0],
            fg=COLOR_ACCENT_LIGHT, bg=COLOR_BG, font=self.header_font
        )
        self.spinner_lbl.pack(side='left', padx=(10, 0))
        
        # Current substatus
        self.substatus_lbl = tk.Label(
            step_info_frame, text='Preparing…',
            fg=COLOR_MUTED, bg=COLOR_BG, font=self.body_font
        )
        self.substatus_lbl.pack(side='left', padx=(15, 0))
        
        # Progress bar with custom styling
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            'Holmes.Horizontal.TProgressbar',
            troughcolor=COLOR_PROGRESS_BG,
            background=COLOR_PROGRESS_FG,
            darkcolor=COLOR_ACCENT_DARK,
            lightcolor=COLOR_ACCENT_LIGHT,
            bordercolor=COLOR_BORDER,
            thickness=20
        )
        
        self.progress = ttk.Progressbar(
            progress_frame, 
            orient='horizontal', 
            length=950,
            mode='determinate',
            style='Holmes.Horizontal.TProgressbar'
        )
        self.progress.pack(fill='x', pady=(0, 8))
        
        # Progress percentage label
        self.progress_pct_lbl = tk.Label(
            progress_frame, text='0%',
            fg=COLOR_ACCENT_LIGHT, bg=COLOR_BG, font=self.header_font
        )
        self.progress_pct_lbl.pack()

        # === Timeline Section ===
        timeline_frame = tk.Frame(self.root, bg=COLOR_BG, height=110)
        timeline_frame.pack(fill='x', padx=25, pady=(5, 0))
        timeline_frame.pack_propagate(False)
        self.timeline_canvas = tk.Canvas(timeline_frame, height=100, bg=COLOR_BG, highlightthickness=0)
        self.timeline_canvas.pack(fill='both', expand=True)
        self.timeline_items_frame = tk.Frame(self.timeline_canvas, bg=COLOR_BG)
        self.timeline_canvas.create_window((0, 0), window=self.timeline_items_frame, anchor='nw')
        self.timeline_items_frame.bind('<Configure>', lambda e: self.timeline_canvas.configure(scrollregion=self.timeline_canvas.bbox('all')))

        # Scrollbar if overflow (horizontal)
        self.timeline_hsb = tk.Scrollbar(timeline_frame, orient='horizontal', command=self.timeline_canvas.xview)
        self.timeline_canvas.configure(xscrollcommand=self.timeline_hsb.set)
        self.timeline_hsb.pack(fill='x', side='bottom')

        # === Log Section ===
        log_frame = tk.Frame(self.root, bg=COLOR_BG)
        log_frame.pack(fill='both', expand=True, padx=25, pady=(10, 15))
        
        # Log header with filters
        log_header = tk.Frame(log_frame, bg=COLOR_BG, height=30)
        log_header.pack(fill='x', pady=(0, 5))
        
        log_title = tk.Label(
            log_header, text='Investigation Log',
            fg=COLOR_FG_BRIGHT, bg=COLOR_BG, font=self.header_font
        )
        log_title.pack(side='left')
        
        # Log filter checkboxes in header
        self._create_filter_checkboxes(log_header)
        
        # Log box with border effect
        log_container = tk.Frame(log_frame, bg=COLOR_BORDER_LIGHT, padx=1, pady=1)
        log_container.pack(fill='both', expand=True)
        
        self.log_box = scrolledtext.ScrolledText(
            log_container, wrap=tk.WORD, state='disabled',
            bg=COLOR_BG_TERTIARY, fg=COLOR_FG, 
            font=self.mono_font,
            borderwidth=0,
            highlightthickness=0,
            insertbackground=COLOR_ACCENT,
            padx=10, pady=10
        )
        self.log_box.pack(fill='both', expand=True)
        
        # Tags for colored log messages
        self.log_box.tag_config('info', foreground=COLOR_INFO)
        self.log_box.tag_config('warn', foreground=COLOR_WARN)
        self.log_box.tag_config('error', foreground=COLOR_ERROR)
        self.log_box.tag_config('success', foreground=COLOR_SUCCESS)
        self.log_box.tag_config('verbose', foreground=COLOR_MUTED_DARK)

        # === Footer Section ===
        footer_frame = tk.Frame(self.root, bg=COLOR_BG_SECONDARY, height=60)
        footer_frame.pack(fill='x', padx=0, pady=0)
        footer_frame.pack_propagate(False)
        
        # Time display
        self.elapsed_lbl = tk.Label(
            footer_frame, text='⏱ Elapsed: 00:00:00 • ETA: —',
            fg=COLOR_MUTED, bg=COLOR_BG_SECONDARY, font=self.body_font
        )
        self.elapsed_lbl.place(x=25, y=20)

        # Action buttons with modern styling
        btn_y = 15
        btn_height = 32
        
        self.close_btn = tk.Button(
            footer_frame, text='✓ Close', 
            bg=COLOR_ACCENT, fg=COLOR_FG_BRIGHT,
            activebackground=COLOR_ACCENT_DARK,
            activeforeground=COLOR_FG_BRIGHT,
            relief='flat',
            state='disabled',
            command=self.root.destroy,
            font=self.body_font,
            cursor='hand2',
            padx=20, pady=6
        )
        self.close_btn.place(x=900, y=btn_y, height=btn_height)
        
        self.stop_btn = tk.Button(
            footer_frame, text='⏹ Stop', 
            bg=COLOR_BG_TERTIARY, fg=COLOR_WARN,
            activebackground=COLOR_BG,
            activeforeground=COLOR_ERROR,
            relief='flat',
            state='disabled',
            font=self.body_font,
            cursor='hand2',
            padx=15, pady=6
        )
        self.stop_btn.place(x=815, y=btn_y, height=btn_height)
        self._stop_cb = None
        
        # Bind hover effects to buttons
        self._bind_button_hover(self.close_btn, COLOR_ACCENT, COLOR_ACCENT_DARK)
        self._bind_button_hover(self.stop_btn, COLOR_BG_TERTIARY, COLOR_BG)

    def _bind_button_hover(self, button, normal_color, hover_color):
        """Bind hover effects to a button"""
        def on_enter(e):
            if button['state'] == 'normal':
                button.config(bg=hover_color)
        
        def on_leave(e):
            if button['state'] == 'normal':
                button.config(bg=normal_color)
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)

    def _create_filter_checkboxes(self, parent):
        """Create log filter checkboxes"""
        filter_frame = tk.Frame(parent, bg=COLOR_BG)
        filter_frame.pack(side='right')
        
        # Verbose filter
        self.filter_verbose = tk.Checkbutton(
            filter_frame, text='Verbose', bg=COLOR_BG, fg=COLOR_MUTED,
            activebackground=COLOR_BG, selectcolor=COLOR_BG_TERTIARY,
            font=self.small_font, command=self._toggle_verbose
        )
        self.filter_verbose.var = tk.BooleanVar(value=False)
        self.filter_verbose.config(variable=self.filter_verbose.var)
        self.filter_verbose.pack(side='left', padx=5)
        
        self.filter_info = tk.Checkbutton(
            filter_frame, text='Info', bg=COLOR_BG, fg=COLOR_INFO,
            activebackground=COLOR_BG, selectcolor=COLOR_BG_TERTIARY,
            font=self.small_font, command=self._toggle_info
        )
        self.filter_info.var = tk.BooleanVar(value=True)
        self.filter_info.config(variable=self.filter_info.var)
        self.filter_info.pack(side='left', padx=5)

        self.filter_warn = tk.Checkbutton(
            filter_frame, text='Warnings', bg=COLOR_BG, fg=COLOR_WARN,
            activebackground=COLOR_BG, selectcolor=COLOR_BG_TERTIARY,
            font=self.small_font, command=self._toggle_warn
        )
        self.filter_warn.var = tk.BooleanVar(value=True)
        self.filter_warn.config(variable=self.filter_warn.var)
        self.filter_warn.pack(side='left', padx=5)

        self.filter_error = tk.Checkbutton(
            filter_frame, text='Errors', bg=COLOR_BG, fg=COLOR_ERROR,
            activebackground=COLOR_BG, selectcolor=COLOR_BG_TERTIARY,
            font=self.small_font, command=self._toggle_error
        )
        self.filter_error.var = tk.BooleanVar(value=True)
        self.filter_error.config(variable=self.filter_error.var)
        self.filter_error.pack(side='left', padx=5)

    def _start_background_tasks(self):
        """Start background update tasks"""
        self.root.after(100, self._process_queue)
        self.root.after(100, self._spin)
        self.root.after(500, self._tick_time)

    def enqueue(self, item: tuple):
        """Add item to processing queue"""
        self.queue.put(item)

    def _append_log(self, level: str, line: str):
        """Append log message to log box with improved formatting"""
        if not self._filters.get(level, True):
            return
        
        # Limit log lines for performance
        self._log_line_count += 1
        if self._log_line_count > self._max_log_lines:
            self.log_box.configure(state='normal')
            # Delete first 100 lines
            self.log_box.delete('1.0', '100.0')
            self._log_line_count -= 100
            self.log_box.configure(state='disabled')
            
        self.log_box.configure(state='normal')
        # Fade-in simulation: temporarily insert with muted color then recolor after delay
        tag = level if level in ('info', 'warn', 'error', 'success', 'verbose') else 'info'
        fade_tag = f"fade_{self._log_line_count}_{tag}"
        self.log_box.tag_config(fade_tag, foreground=COLOR_MUTED_DARK)
        self.log_box.insert('end', line, fade_tag)
        self.log_box.see('end')
        def _recolor(tag_original=fade_tag, final_tag=tag):
            try:
                self.log_box.tag_config(tag_original, foreground=self.log_box.tag_cget(final_tag, 'foreground'))
            except Exception:
                pass
        self.root.after(250, _recolor)
        self.log_box.configure(state='disabled')

    def set_status(self, text: str):
        """Update status label"""
        self.status_lbl.configure(text=text)

    def set_progress(self, value: int):
        """Set progress bar value and update percentage label"""
        try:
            value = max(0, min(100, int(value)))
            self.progress['value'] = value
            self.progress_pct_lbl.configure(text=f'{value}%')
        except Exception:
            pass

    def animate_progress_to(self, target: int):
        """Animate progress bar to target value smoothly"""
        target = max(0, min(100, int(target)))
        self._anim_target = target
        if self._anim_job is None:
            self._anim_job = self.root.after(10, self._animate_step)

    def _animate_step(self):
        """Single step of smooth progress animation"""
        current = int(self.progress['value'])
        if current == self._anim_target:
            self._anim_job = None
            return
        
        # Smooth acceleration/deceleration
        diff = self._anim_target - current
        step = max(1, abs(diff) // 10)  # Dynamic step size
        
        if diff > 0:
            nxt = min(current + step, self._anim_target)
        else:
            nxt = max(current - step, self._anim_target)
            
        self.set_progress(nxt)
        self._anim_job = self.root.after(10, self._animate_step)

    def _add_timeline_step(self, idx: int, name: str):
        """Add a visual element for a new step to the timeline."""
        row = tk.Frame(self.timeline_items_frame, bg=COLOR_BG, padx=8, pady=4)
        row.pack(side='left')
        icon_lbl = tk.Label(row, text='⏳', fg=COLOR_ACCENT_LIGHT, bg=COLOR_BG, font=self.body_font)
        icon_lbl.pack(side='top')
        name_lbl = tk.Label(row, text=self._trim_name(name), fg=COLOR_MUTED, bg=COLOR_BG, font=self.small_font, wraplength=120, justify='center')
        name_lbl.pack(side='top', pady=(2, 0))
        self._timeline_steps.append({'idx': idx, 'name': name, 'status': 'pending', 'widget': icon_lbl})
        # Auto-scroll to end
        self.root.after(50, lambda: self.timeline_canvas.xview_moveto(1.0))

    def _trim_name(self, name: str, max_len: int = 28) -> str:
        return name if len(name) <= max_len else name[:max_len-1] + '…'

    def _mark_timeline_step(self, idx: int, success: bool):
        """Update timeline icon for a step result with animation fade."""
        for step in self._timeline_steps:
            if step['idx'] == idx:
                step['status'] = 'ok' if success else 'fail'
                widget = step['widget']
                target_color = COLOR_SUCCESS if success else COLOR_ERROR
                target_icon = '✓' if success else '✗'
                # Fade animation using incremental color adjustments
                self._animate_icon_transition(widget, target_icon, target_color)
                if not success:
                    self._show_toast(f"Step {idx} failed", error=True)
                break

    def _animate_icon_transition(self, widget, final_text: str, final_color: str, steps: int = 6, delay: int = 40):
        """Animate icon from spinner to final state by pulsing color."""
        def _step(n=0):
            if n >= steps:
                widget.configure(text=final_text, fg=final_color)
                return
            # Alternate color between accent light/dark for pulse
            color = COLOR_ACCENT_LIGHT if n % 2 == 0 else COLOR_ACCENT_DARK
            widget.configure(fg=color)
            self.root.after(delay, lambda: _step(n + 1))
        _step()

    def _show_toast(self, message: str, duration_ms: int = 3000, error: bool = False):
        """Show a toast notification (floating, fades)."""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        bg = COLOR_BG_SECONDARY if not error else COLOR_ERROR
        fg = COLOR_FG_BRIGHT if not error else COLOR_BG
        frame = tk.Frame(toast, bg=bg)
        frame.pack(fill='both', expand=True)
        lbl = tk.Label(frame, text=message, bg=bg, fg=fg, font=self.body_font, padx=16, pady=10)
        lbl.pack()
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() - toast.winfo_reqwidth() - 28
        y = self.root.winfo_rooty() + self.root.winfo_height() - toast.winfo_reqheight() - 80
        toast.geometry(f"+{x}+{y}")
        try:
            toast.attributes('-alpha', 0.0)
        except Exception:
            pass
        self._toast_windows.append(toast)
        def fade_in(step=0):
            try:
                alpha = min(1.0, step / 10.0)
                toast.attributes('-alpha', alpha)
            except Exception:
                pass
            if step < 10:
                toast.after(25, lambda: fade_in(step + 1))
            else:
                toast.after(duration_ms, fade_out)
        def fade_out(step=10):
            try:
                alpha = max(0.0, step / 10.0)
                toast.attributes('-alpha', alpha)
            except Exception:
                pass
            if step > 0:
                toast.after(25, lambda: fade_out(step - 1))
            else:
                if toast in self._toast_windows:
                    self._toast_windows.remove(toast)
                toast.destroy()
        fade_in()

    def enable_close(self):
        """Enable close button and show completion summary"""
        self.close_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')

        # Count results from timeline
        ok = sum(1 for s in self._timeline_steps if s.get('status') == 'ok')
        fail = sum(1 for s in self._timeline_steps if s.get('status') == 'fail')
        total = len(self._timeline_steps)

        if fail > 0:
            self.spinner_lbl.configure(text='!', fg=COLOR_WARN)
            self.status_lbl.configure(text=f'Done — {ok}/{total} succeeded, {fail} failed', fg=COLOR_WARN)
            self._show_toast(f'Done — {fail} step(s) failed', error=True)
        else:
            self.spinner_lbl.configure(text='✓', fg=COLOR_SUCCESS)
            self.status_lbl.configure(text='Investigation complete', fg=COLOR_SUCCESS)
            self._show_toast('Investigation complete ✓')

        # Show elapsed time in substatus
        elapsed = int(time.time() - self._start_time)
        mm, ss = divmod(elapsed, 60)
        hh, mm = divmod(mm, 60)
        self.substatus_lbl.configure(text=f'Completed in {hh:02d}:{mm:02d}:{ss:02d}')

    def set_stop_callback(self, cb: Callable):
        """Set callback for stop button"""
        self._stop_cb = cb
        def _on_click():
            self.stop_btn.configure(state='disabled')
            if self._stop_cb:
                self._stop_cb()
                self.enqueue(('status', 'Stopping investigation…'))
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
                    self._add_timeline_step(idx, name)
                elif kind == 'step_result':
                    _, idx, success = item
                    self._mark_timeline_step(idx, success)
        except queue.Empty:
            pass
            
        self.root.after(100, self._process_queue)

    def _spin(self):
        """Update spinner animation"""
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
        self.spinner_lbl.configure(text=self._spinner_frames[self._spinner_index])
        self.root.after(100, self._spin)

    def _tick_time(self):
        """Update elapsed time display"""
        elapsed = max(0, int(time.time() - self._start_time))
        mm, ss = divmod(elapsed, 60)
        hh, mm = divmod(mm, 60)
        self.elapsed_lbl.configure(text=f"⏱ Elapsed: {hh:02d}:{mm:02d}:{ss:02d} • ETA: {self._last_eta}")
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
    
    def _toggle_verbose(self):
        """Toggle verbose log filter"""
        self._filters['verbose'] = bool(self.filter_verbose.var.get())

    def run(self):
        """Start UI main loop"""
        self.root.mainloop()

    def show_selection(self, registry: List[Dict[str, Any]], on_start: Callable, preselected_ids: Optional[List[str]] = None):
        """Show compact component selection dialog with two-column layout"""
        dlg = tk.Toplevel(self.root)
        dlg.title('Select Tools')
        dlg.configure(bg=COLOR_BG)
        dlg.geometry('1020x720')
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(True, True)

        # === Compact Header ===
        header = tk.Frame(dlg, bg=COLOR_BG_SECONDARY, height=55)
        header.pack(fill='x')
        header.pack_propagate(False)

        title = tk.Label(
            header, text='🔍 Select Tools',
            fg=COLOR_ACCENT_LIGHT, bg=COLOR_BG_SECONDARY,
            font=self.header_font
        )
        title.pack(side='left', padx=14, pady=12)

        subtitle = tk.Label(
            header, text='Choose forensics tools to install',
            fg=COLOR_MUTED, bg=COLOR_BG_SECONDARY,
            font=self.small_font
        )
        subtitle.pack(side='left', padx=(0, 10), pady=12)

        # Search entry in header
        search_var = tk.StringVar(value='')
        search_entry = tk.Entry(
            header, textvariable=search_var, bg=COLOR_BG_TERTIARY,
            fg=COLOR_FG, insertbackground=COLOR_FG, font=self.body_font,
            relief='flat', width=24
        )
        search_entry.pack(side='right', padx=14, pady=12)
        tk.Label(header, text='Search:', fg=COLOR_MUTED, bg=COLOR_BG_SECONDARY,
                 font=self.small_font).pack(side='right', pady=12)

        # === Counter ===
        total_items = sum(len(cat.get('items', [])) for cat in registry)
        counter_var = tk.StringVar(value=f'0 / {total_items} selected')
        counter_lbl = tk.Label(dlg, textvariable=counter_var, fg=COLOR_MUTED, bg=COLOR_BG,
                               font=self.small_font)
        counter_lbl.pack(anchor='w', padx=14, pady=(4, 0))

        # === Scrollable content ===
        container = tk.Frame(dlg, bg=COLOR_BG)
        container.pack(fill='both', expand=True, padx=10, pady=4)

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
        item_rows = []  # (widget, searchable_text)

        def _update_counter(*_a):
            n = sum(1 for v in vars_map.values() if v.get())
            counter_var.set(f'{n} / {total_items} selected')

        for cat in registry:
            # Compact category header
            cat_frame = tk.Frame(frame, bg=COLOR_BG_SECONDARY, padx=8, pady=4)
            cat_frame.pack(fill='x', pady=(5, 1))

            items = cat.get('items', [])
            count = len(items)
            cat_lbl = tk.Label(
                cat_frame, text=f"{cat['name']}  ({count})",
                fg=COLOR_FG_BRIGHT, bg=COLOR_BG_SECONDARY,
                font=self.header_font
            )
            cat_lbl.pack(anchor='w')

            # Two-column items grid
            items_frame = tk.Frame(frame, bg=COLOR_BG)
            items_frame.pack(fill='x', padx=4, pady=(0, 2))
            items_frame.grid_columnconfigure(0, weight=1)
            items_frame.grid_columnconfigure(1, weight=1)

            for idx, item in enumerate(items):
                default_selected = (
                    preselected_ids is None and item.get('default', True)
                ) or (
                    preselected_ids is not None and item['id'] in preselected_ids
                )
                var = tk.BooleanVar(value=default_selected)
                var.trace_add('write', _update_counter)
                vars_map[item['id']] = var

                col = idx % 2
                row_num = idx // 2

                cell = tk.Frame(items_frame, bg=COLOR_BG, padx=4, pady=1)
                cell.grid(row=row_num, column=col, sticky='ew')

                desc_text = item.get('description', '')
                display = item['name']
                if desc_text:
                    display += f'  —  {desc_text}'

                cb = tk.Checkbutton(
                    cell, text=display,
                    bg=COLOR_BG, fg=COLOR_FG, variable=var,
                    activebackground=COLOR_BG, selectcolor=COLOR_BG_TERTIARY,
                    font=self.body_font, cursor='hand2', anchor='w',
                    wraplength=440
                )
                cb.pack(side='left', fill='x')

                searchable = (item.get('name', '') + ' ' + desc_text).lower()
                item_rows.append((cell, searchable))

        _update_counter()

        # === Compact Footer ===
        footer = tk.Frame(dlg, bg=COLOR_BG_SECONDARY, height=48)
        footer.pack(fill='x')
        footer.pack_propagate(False)

        btns = tk.Frame(footer, bg=COLOR_BG_SECONDARY)
        btns.pack(fill='x', padx=14, pady=8)

        def select_all():
            for v in vars_map.values():
                v.set(True)

        def deselect_all():
            for v in vars_map.values():
                v.set(False)

        tk.Button(
            btns, text='☑ All', command=select_all,
            bg=COLOR_BG_TERTIARY, fg=COLOR_INFO,
            activebackground=COLOR_BG, relief='flat',
            font=self.small_font, cursor='hand2', padx=8, pady=4
        ).pack(side='left')

        tk.Button(
            btns, text='☐ None', command=deselect_all,
            bg=COLOR_BG_TERTIARY, fg=COLOR_WARN,
            activebackground=COLOR_BG, relief='flat',
            font=self.small_font, cursor='hand2', padx=8, pady=4
        ).pack(side='left', padx=6)

        def start():
            selected = [k for k, v in vars_map.items() if v.get()]
            dlg.destroy()
            on_start(selected)

        def cancel():
            dlg.destroy()
            self.root.destroy()

        tk.Button(
            btns, text='Cancel', command=cancel,
            bg=COLOR_BG_TERTIARY, fg=COLOR_MUTED,
            activebackground=COLOR_BG, relief='flat',
            font=self.small_font, cursor='hand2', padx=10, pady=4
        ).pack(side='right', padx=(6, 0))

        start_btn = tk.Button(
            btns, text='▶ Install Selected', command=start,
            bg=COLOR_ACCENT, fg=COLOR_FG_BRIGHT,
            activebackground=COLOR_ACCENT_DARK, relief='flat',
            font=self.header_font, cursor='hand2', padx=14, pady=4
        )
        start_btn.pack(side='right')
        self._bind_button_hover(start_btn, COLOR_ACCENT, COLOR_ACCENT_DARK)

        # Search filter
        def on_search(*_):
            q = (search_var.get() or '').lower().strip()
            for widget, text in item_rows:
                if not q or q in text:
                    widget.grid()
                else:
                    widget.grid_remove()
        search_var.trace_add('write', on_search)


def is_tk_available() -> bool:
    """Check if Tkinter is available"""
    return TK_AVAILABLE

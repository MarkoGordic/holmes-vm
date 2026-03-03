#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern UI window for Holmes VM Setup using CustomTkinter
Beautiful, native-looking interface with proper scrolling and visibility
"""

import queue
import time
from typing import List, Dict, Any, Callable, Optional

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    ctk = None

# Add tkinter for Canvas
import tkinter as tk

from .colors import *


class ModernUI:
    """Modern UI window for Holmes VM setup with CustomTkinter"""
    
    def __init__(self, title: str):
        if not CTK_AVAILABLE:
            raise RuntimeError('CustomTkinter not available')
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.root = ctk.CTk()
        self.root.title(title)
        self.root.geometry('1100x750')
        
        # Configure grid weight
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.queue = queue.Queue()
        self._start_time = time.time()
        self._last_eta = '—'
        self._filters = {'info': True, 'warn': True, 'error': True, 'success': True, 'verbose': False}
        self._is_complete = False
        # Animation state
        self._spinner_frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
        self._spinner_index = 0
        self._spin_job = None
        self._progress_target = 0.0
        self._progress_job = None
        # Timeline state
        self._timeline_steps: List[Dict[str, Any]] = []  # {'idx': int, 'icon': CTkLabel}
        self._timeline_col = 0
        
        self._setup_ui()
        self._start_background_tasks()
    
    def _setup_ui(self):
        """Setup all UI components"""
        
        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color=COLOR_BG)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # === Header ===
        header_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BG_SECONDARY, height=120)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔍 HOLMES VM INSTALLATION",
            font=("Segoe UI", 24, "bold"),
            text_color=COLOR_ACCENT_LIGHT
        )
        title_label.grid(row=0, column=0, pady=(20, 5))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Digital Forensics Environment • Elementary, my dear Watson",
            font=("Segoe UI", 11),
            text_color=COLOR_MUTED
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 5))
        
        # Current status (large and visible)
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Initializing installation...",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_ACCENT
        )
        self.status_label.grid(row=2, column=0, pady=(5, 15))
        
        # === Progress Section ===
        progress_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BG, height=140)
        progress_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 0))
        progress_frame.grid_columnconfigure(0, weight=0)
        progress_frame.grid_columnconfigure(1, weight=0)
        progress_frame.grid_columnconfigure(2, weight=1)
        
        # Step info
        step_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        step_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        step_frame.grid_columnconfigure(0, weight=0)
        step_frame.grid_columnconfigure(1, weight=0)
        step_frame.grid_columnconfigure(2, weight=1)
        
        self.step_label = ctk.CTkLabel(
            step_frame,
            text="Step 0/0",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_ACCENT
        )
        self.step_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Animated spinner next to step
        self.spinner_label = ctk.CTkLabel(
            step_frame,
            text=self._spinner_frames[0],
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_ACCENT_LIGHT
        )
        self.spinner_label.grid(row=0, column=1, sticky="w")
        
        self.substatus_label = ctk.CTkLabel(
            step_frame,
            text="Preparing...",
            font=("Segoe UI", 12),
            text_color=COLOR_FG
        )
        self.substatus_label.grid(row=0, column=2, sticky="w")
        
        # Progress bar (modern, deterministic)
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=25,
            progress_color=COLOR_ACCENT,
            fg_color=COLOR_BG_TERTIARY
        )
        self.progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.progress_bar.set(0)
        
        # Progress percentage
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_ACCENT_LIGHT
        )
        self.progress_label.grid(row=2, column=0, columnspan=3)

        # === Timeline Section ===
        timeline_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BG, height=140)
        timeline_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(6, 0))
        timeline_frame.grid_columnconfigure(0, weight=1)
        timeline_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable timeline (horizontal) using tkinter.Canvas (no visible scrollbar)
        self.timeline_canvas = tk.Canvas(timeline_frame, height=130, bg=COLOR_BG, highlightthickness=0, bd=0)
        self.timeline_canvas.grid(row=0, column=0, sticky='nsew')
        self.timeline_inner = ctk.CTkFrame(self.timeline_canvas, fg_color='transparent')
        self.timeline_canvas.create_window((0, 0), window=self.timeline_inner, anchor='nw')
        self.timeline_inner.bind('<Configure>', lambda e: self.timeline_canvas.configure(scrollregion=self.timeline_canvas.bbox('all')))
        # Gesture-based horizontal scroll (wheel + drag)
        self.timeline_canvas.bind('<Enter>', lambda e: self._bind_timeline_scroll())
        self.timeline_canvas.bind('<Leave>', lambda e: self._unbind_timeline_scroll())
        self.timeline_canvas.bind('<ButtonPress-1>', self._timeline_drag_start)
        self.timeline_canvas.bind('<B1-Motion>', self._timeline_drag_move)
        self._drag_last_x = None
        self._timeline_col = 0
        self._timeline_steps = []
        
        # === Log Section with Scrollable Frame ===
        log_container = ctk.CTkFrame(main_frame, fg_color=COLOR_BG)
        log_container.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10, 10))
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(1, weight=1)
        
        # Log header with filters
        log_header = ctk.CTkFrame(log_container, fg_color="transparent", height=40)
        log_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        log_header.grid_columnconfigure(1, weight=1)
        
        log_title = ctk.CTkLabel(
            log_header,
            text="Installation Log",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_FG_BRIGHT
        )
        log_title.grid(row=0, column=0, sticky="w")
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(log_header, fg_color="transparent")
        filter_frame.grid(row=0, column=1, sticky="e")
        
        self.verbose_var = ctk.BooleanVar(value=False)
        self.info_var = ctk.BooleanVar(value=True)
        self.warn_var = ctk.BooleanVar(value=True)
        self.error_var = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(
            filter_frame, text="Verbose", variable=self.verbose_var,
            command=self._toggle_verbose, fg_color=COLOR_ACCENT,
            text_color=COLOR_MUTED, font=("Segoe UI", 10)
        ).pack(side="left", padx=5)
        
        ctk.CTkCheckBox(
            filter_frame, text="Info", variable=self.info_var,
            command=self._toggle_info, fg_color=COLOR_ACCENT,
            text_color=COLOR_INFO, font=("Segoe UI", 10)
        ).pack(side="left", padx=5)
        
        ctk.CTkCheckBox(
            filter_frame, text="Warnings", variable=self.warn_var,
            command=self._toggle_warn, fg_color=COLOR_ACCENT,
            text_color=COLOR_WARN, font=("Segoe UI", 10)
        ).pack(side="left", padx=5)
        
        ctk.CTkCheckBox(
            filter_frame, text="Errors", variable=self.error_var,
            command=self._toggle_error, fg_color=COLOR_ACCENT,
            text_color=COLOR_ERROR, font=("Segoe UI", 10)
        ).pack(side="left", padx=5)
        
        # Scrollable log textbox
        self.log_textbox = ctk.CTkTextbox(
            log_container,
            fg_color=COLOR_BG_TERTIARY,
            text_color=COLOR_FG,
            font=("Consolas", 10),
            wrap="word",
            activate_scrollbars=True
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew")
        self.log_textbox.configure(state="disabled")
        
        # === Footer ===
        footer_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BG_SECONDARY, height=70)
        footer_frame.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # Time info
        self.time_label = ctk.CTkLabel(
            footer_frame,
            text="⏱ Elapsed: 00:00:00 • ETA: —",
            font=("Segoe UI", 11),
            text_color=COLOR_MUTED
        )
        self.time_label.grid(row=0, column=0, sticky="w", padx=20, pady=20)
        
        # Buttons
        button_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="e", padx=20, pady=20)
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="⏹ Stop",
            width=100,
            height=35,
            fg_color=COLOR_BG_TERTIARY,
            hover_color=COLOR_MUTED_DARK,
            text_color=COLOR_FG_BRIGHT,
            font=("Segoe UI", 11, "bold"),
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=(0, 10))
        
        self.close_button = ctk.CTkButton(
            button_frame,
            text="✓ Close",
            width=120,
            height=35,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_DARK,
            text_color=COLOR_FG_BRIGHT,
            font=("Segoe UI", 11, "bold"),
            command=self.root.destroy,
            state="disabled"
        )
        self.close_button.pack(side="left")
    
    def _start_background_tasks(self):
        """Start background update tasks"""
        self.root.after(100, self._process_queue)
        self.root.after(500, self._tick_time)
        # Start spinner and subtle progress animation loop
        self.root.after(120, self._spin)
    
    def enqueue(self, item: tuple):
        """Add item to processing queue"""
        self.queue.put(item)
    
    def _append_log(self, level: str, line: str):
        """Append log message to textbox"""
        if not self._filters.get(level, True):
            return
        
        self.log_textbox.configure(state="normal")
        # Add light prefix icons for readability
        prefix = {
            'info': '→ ',
            'warn': '⚠ ',
            'error': '✗ ',
            'success': '✓ ',
            'verbose': '… '
        }.get(level, '')
        self.log_textbox.insert("end", prefix + line)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
    
    def set_status(self, text: str):
        """Update main status label"""
        self.status_label.configure(text=text)
    
    def set_progress(self, value: float):
        """Set progress bar value (0-100)"""
        value = max(0.0, min(100.0, float(value)))
        self.progress_bar.set(value / 100.0)
        self.progress_label.configure(text=f"{int(value)}%")
    
    def animate_progress_to(self, target: float):
        """Animate progress to target smoothly"""
        try:
            self._progress_target = max(0.0, min(100.0, float(target)))
            if self._progress_job is None:
                self._progress_job = self.root.after(10, self._progress_step)
        except Exception:
            self.set_progress(target)
    
    def _progress_step(self):
        current = float(self.progress_bar._determinate_value) * 100.0  # internal value in [0..1]
        diff = self._progress_target - current
        if abs(diff) < 0.5:
            self.set_progress(self._progress_target)
            self._progress_job = None
            return
        # Easing: move 15% towards target per tick, min step 0.5
        step = max(0.5, abs(diff) * 0.15)
        next_val = current + step if diff > 0 else current - step
        self.set_progress(next_val)
        self._progress_job = self.root.after(16, self._progress_step)
    
    def _spin(self):
        """Update spinner animation and pulse status color subtly"""
        try:
            self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
            self.spinner_label.configure(text=self._spinner_frames[self._spinner_index])
            # Subtle pulse by toggling between two accent tones
            if self._spinner_index % 2 == 0:
                self.status_label.configure(text_color=COLOR_ACCENT)
            else:
                self.status_label.configure(text_color=COLOR_ACCENT_LIGHT)
        finally:
            self._spin_job = self.root.after(100, self._spin)
    
    def _show_toast(self, message: str, duration_ms: int = 2500):
        """Show a lightweight toast notification bottom-right"""
        toast = ctk.CTkToplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(fg_color=COLOR_BG_SECONDARY)
        lbl = ctk.CTkLabel(toast, text=message, font=("Segoe UI", 11, "bold"), text_color=COLOR_FG_BRIGHT)
        lbl.pack(padx=16, pady=10)
        # Position bottom-right relative to root
        self.root.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        tw = toast.winfo_reqwidth()
        th = toast.winfo_reqheight()
        x = rx + rw - tw - 24
        y = ry + rh - th - 24
        toast.geometry(f"+{x}+{y}")
        try:
            toast.attributes('-alpha', 0.0)
        except Exception:
            pass
        
        def fade_in(step=0):
            try:
                alpha = min(1.0, 0.1 * step)
                toast.attributes('-alpha', alpha)
            except Exception:
                pass
            if alpha < 1.0:
                toast.after(30, lambda: fade_in(step + 1))
            else:
                toast.after(duration_ms, fade_out)
        
        def fade_out(step=10):
            try:
                alpha = max(0.0, 0.1 * step)
                toast.attributes('-alpha', alpha)
            except Exception:
                pass
            if alpha > 0.0:
                toast.after(30, lambda: fade_out(step - 1))
            else:
                toast.destroy()
        
        fade_in()

    # Timeline helpers
    def _add_timeline_step(self, idx: int, name: str):
        item = ctk.CTkFrame(self.timeline_inner, fg_color="transparent")
        item.grid(row=0, column=self._timeline_col, padx=10, pady=6, sticky='n')
        self._timeline_col += 1
        icon = ctk.CTkLabel(item, text='⏳', text_color=COLOR_ACCENT_LIGHT, font=("Segoe UI", 14, "bold"))
        icon.pack()
        label = ctk.CTkLabel(item, text=self._trim_name(name), text_color=COLOR_MUTED, font=("Segoe UI", 10), wraplength=150, justify='center')
        label.pack(pady=(2, 8))
        self._timeline_steps.append({'idx': idx, 'icon': icon})
        # Auto-scroll to newest step
        self.root.after(50, self._scroll_timeline_to_end)

    def _scroll_timeline_to_end(self):
        try:
            self.timeline_canvas.xview_moveto(1.0)
        except Exception:
            pass

    def _trim_name(self, name: str, max_len: int = 28) -> str:
        return name if len(name) <= max_len else name[:max_len-1] + '…'

    def _mark_timeline_step(self, idx: int, success: bool):
        for st in self._timeline_steps:
            if st['idx'] == idx:
                icon_widget = st['icon']
                final_color = COLOR_SUCCESS if success else COLOR_ERROR
                final_icon = '✓' if success else '✗'
                self._animate_icon_transition(icon_widget, final_icon, final_color)
                if not success:
                    self._show_toast(f"Step {idx} failed")
                break

    def _animate_icon_transition(self, widget, final_text: str, final_color: str, steps: int = 6, delay: int = 40):
        def _step(n=0):
            if n >= steps:
                widget.configure(text=final_text, text_color=final_color)
                return
            color = COLOR_ACCENT_LIGHT if n % 2 == 0 else COLOR_ACCENT_DARK
            widget.configure(text_color=color)
            self.root.after(delay, lambda: _step(n + 1))
        _step()
    
    def enable_close(self):
        """Enable close button and show completion"""
        self._is_complete = True
        self.close_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(
            text="✓ Installation Complete!",
            text_color=COLOR_SUCCESS
        )
        self.progress_bar.configure(progress_color=COLOR_SUCCESS)
        # Toast notification
        self._show_toast("Installation complete")
    
    def set_stop_callback(self, cb: Callable):
        """Set callback for stop button"""
        self._stop_cb = cb
        def _on_click():
            self.stop_button.configure(state="disabled")
            if self._stop_cb:
                self._stop_cb()
                self.enqueue(('status', 'Stopping installation…'))
        self.stop_button.configure(command=_on_click)
    
    def set_stop_enabled(self, enabled: bool):
        """Enable/disable stop button"""
        self.stop_button.configure(state=("normal" if enabled else "disabled"))
    
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
                    self.step_label.configure(text=f"Step {idx}/{total}")
                    self.substatus_label.configure(text=name)
                    self._add_timeline_step(idx, name)
                elif kind == 'step_result':
                    _, idx, success = item
                    self._mark_timeline_step(idx, success)
        except queue.Empty:
            pass
        
        self.root.after(100, self._process_queue)
    
    def _tick_time(self):
        """Update elapsed time display"""
        elapsed = max(0, int(time.time() - self._start_time))
        mm, ss = divmod(elapsed, 60)
        hh, mm = divmod(mm, 60)
        self.time_label.configure(text=f"⏱ Elapsed: {hh:02d}:{mm:02d}:{ss:02d} • ETA: {self._last_eta}")
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
        self._filters['info'] = self.info_var.get()
    
    def _toggle_warn(self):
        """Toggle warning log filter"""
        self._filters['warn'] = self.warn_var.get()
    
    def _toggle_error(self):
        """Toggle error log filter"""
        self._filters['error'] = self.error_var.get()
    
    def _toggle_verbose(self):
        """Toggle verbose log filter"""
        self._filters['verbose'] = self.verbose_var.get()
    
    def run(self):
        """Start UI main loop"""
        self.root.mainloop()
    
    def show_selection(self, registry: List[Dict[str, Any]], on_start: Callable, preselected_ids: Optional[List[str]] = None):
        """Show compact component selection dialog with two-column layout, search, and collapsible categories"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Tools")
        dialog.geometry("1060x760")
        dialog.transient(self.root)
        dialog.grab_set()

        # Configure grid
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(2, weight=1)

        # --- Compact Header ---
        header = ctk.CTkFrame(dialog, fg_color=COLOR_BG_SECONDARY, height=70)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title = ctk.CTkLabel(
            header, text="🔍 Select Tools",
            font=("Segoe UI", 15, "bold"), text_color=COLOR_ACCENT_LIGHT
        )
        title.grid(row=0, column=0, sticky='w', padx=16, pady=(12, 2))

        subtitle = ctk.CTkLabel(
            header, text="Choose forensics tools to install",
            font=("Segoe UI", 10), text_color=COLOR_MUTED
        )
        subtitle.grid(row=1, column=0, sticky='w', padx=16, pady=(0, 8))

        # Search bar
        search_var = ctk.StringVar(value="")
        search_entry = ctk.CTkEntry(
            header, placeholder_text="Search…", textvariable=search_var,
            width=220, height=28, font=("Segoe UI", 10)
        )
        search_entry.grid(row=0, column=1, rowspan=2, sticky='e', padx=16)

        # --- Counter label (selected / total) ---
        counter_frame = ctk.CTkFrame(dialog, fg_color=COLOR_BG, height=22)
        counter_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(6, 0))
        counter_frame.grid_columnconfigure(0, weight=1)

        total_items = sum(len(cat.get('items', [])) for cat in registry)
        counter_label = ctk.CTkLabel(
            counter_frame, text=f"0 / {total_items} selected",
            font=("Segoe UI", 10), text_color=COLOR_MUTED
        )
        counter_label.grid(row=0, column=0, sticky='w')

        # Scrollable frame for selection
        scroll_frame = ctk.CTkScrollableFrame(
            dialog, fg_color=COLOR_BG, label_text="", label_fg_color=COLOR_BG
        )
        scroll_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 4))
        # Two columns for items
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Build selection UI
        vars_map: Dict[str, Any] = {}
        cat_to_items: Dict[str, List[str]] = {}
        item_rows: List[tuple] = []  # (frame, searchable_text)

        def _update_counter(*_a):
            n = sum(1 for v in vars_map.values() if v.get())
            counter_label.configure(text=f"{n} / {total_items} selected")

        grid_row = 0
        for cat in registry:
            cat_key = cat.get('id', cat.get('name', ''))
            items = cat.get('items', [])
            count = len(items)
            cat_to_items[cat_key] = []

            # --- Category header row ---
            cat_frame = ctk.CTkFrame(scroll_frame, fg_color=COLOR_BG_SECONDARY, corner_radius=6)
            cat_frame.grid(row=grid_row, column=0, sticky="ew", pady=(6, 2), padx=2)
            cat_frame.grid_columnconfigure(1, weight=1)
            grid_row += 1

            expanded = {'val': True}
            toggle_btn = ctk.CTkButton(
                cat_frame, text="▾", width=22, height=22,
                fg_color=COLOR_BG_TERTIARY, hover_color=COLOR_MUTED_DARK,
                text_color=COLOR_FG, font=("Segoe UI", 10)
            )
            toggle_btn.grid(row=0, column=0, padx=(6, 4), pady=5)

            cat_label = ctk.CTkLabel(
                cat_frame, text=f"{cat['name']}",
                font=("Segoe UI", 11, "bold"), text_color=COLOR_FG_BRIGHT, anchor="w"
            )
            cat_label.grid(row=0, column=1, sticky="w", pady=5)

            count_badge = ctk.CTkLabel(
                cat_frame, text=f"{count}",
                font=("Segoe UI", 9), text_color=COLOR_MUTED,
                width=28
            )
            count_badge.grid(row=0, column=2, padx=(2, 4), pady=5)

            actions_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=3, sticky="e", padx=6)

            def make_cat_toggle(ids: List[str], value: bool):
                def _toggle():
                    for _id in ids:
                        if _id in vars_map:
                            vars_map[_id].set(value)
                    _update_counter()
                return _toggle

            # --- Items container (two-column grid) ---
            items_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            items_frame.grid(row=grid_row, column=0, sticky="ew", padx=4, pady=(0, 2))
            items_frame.grid_columnconfigure(0, weight=1)
            items_frame.grid_columnconfigure(1, weight=1)
            grid_row += 1

            for item_idx, item in enumerate(items):
                default_selected = (
                    preselected_ids is None and item.get('default', True)
                ) or (
                    preselected_ids is not None and item['id'] in preselected_ids
                )
                var = ctk.BooleanVar(value=default_selected)
                var.trace_add('write', _update_counter)
                vars_map[item['id']] = var
                cat_to_items[cat_key].append(item['id'])

                col = item_idx % 2
                row = item_idx // 2

                item_frame = ctk.CTkFrame(items_frame, fg_color="transparent")
                item_frame.grid(row=row, column=col, sticky="ew", pady=1, padx=(4, 8))
                item_frame.grid_columnconfigure(0, weight=0)
                item_frame.grid_columnconfigure(1, weight=1)

                # Compact checkbox
                cb = ctk.CTkCheckBox(
                    item_frame, text="", variable=var,
                    fg_color=COLOR_ACCENT, width=18, height=18,
                    checkbox_width=16, checkbox_height=16
                )
                cb.grid(row=0, column=0, sticky="w", padx=(4, 2))

                # Name + inline description
                desc_text = item.get('description', '')
                display_text = item['name']
                if desc_text:
                    display_text += f"  —  {desc_text}"

                name_label = ctk.CTkLabel(
                    item_frame, text=display_text,
                    font=("Segoe UI", 10), text_color=COLOR_FG, anchor="w",
                    wraplength=440
                )
                name_label.grid(row=0, column=1, sticky="w", padx=2)

                # Make label click toggle checkbox
                name_label.bind('<Button-1>', lambda e, v=var: v.set(not v.get()))

                searchable = (item.get('name', '') + ' ' + desc_text).lower()
                item_rows.append((item_frame, searchable))

            ids = cat_to_items[cat_key]
            ctk.CTkButton(
                actions_frame, text="All", command=make_cat_toggle(ids, True),
                fg_color=COLOR_BG_TERTIARY, hover_color=COLOR_MUTED_DARK,
                text_color=COLOR_INFO, width=40, height=22, font=("Segoe UI", 9)
            ).grid(row=0, column=0, padx=(0, 3))
            ctk.CTkButton(
                actions_frame, text="None", command=make_cat_toggle(ids, False),
                fg_color=COLOR_BG_TERTIARY, hover_color=COLOR_MUTED_DARK,
                text_color=COLOR_WARN, width=42, height=22, font=("Segoe UI", 9)
            ).grid(row=0, column=1)

            def toggle_items(frame=items_frame, btn=toggle_btn, state=expanded):
                state['val'] = not state['val']
                if state['val']:
                    btn.configure(text='▾')
                    frame.grid()
                else:
                    btn.configure(text='▸')
                    frame.grid_remove()
            toggle_btn.configure(command=toggle_items)

        # Initial counter update
        _update_counter()

        # --- Compact Footer ---
        footer = ctk.CTkFrame(dialog, fg_color=COLOR_BG_SECONDARY, height=50)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        left_buttons = ctk.CTkFrame(footer, fg_color="transparent")
        left_buttons.grid(row=0, column=0, sticky="w", padx=14, pady=10)

        def select_all():
            for v in vars_map.values():
                v.set(True)

        def deselect_all():
            for v in vars_map.values():
                v.set(False)

        ctk.CTkButton(
            left_buttons, text="☑ All", command=select_all,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
            text_color=COLOR_FG_BRIGHT, width=70, height=28, font=("Segoe UI", 10)
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            left_buttons, text="☐ None", command=deselect_all,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
            text_color=COLOR_FG_BRIGHT, width=70, height=28, font=("Segoe UI", 10)
        ).pack(side="left", padx=(0, 10))

        right_buttons = ctk.CTkFrame(footer, fg_color="transparent")
        right_buttons.grid(row=0, column=1, sticky="e", padx=14, pady=10)

        def cancel():
            dialog.destroy()
            self.root.destroy()

        def start():
            selected = [k for k, v in vars_map.items() if v.get()]
            dialog.destroy()
            on_start(selected)

        ctk.CTkButton(
            right_buttons, text="Cancel", command=cancel,
            fg_color=COLOR_BG_TERTIARY, hover_color=COLOR_MUTED_DARK,
            text_color=COLOR_MUTED, width=80, height=28, font=("Segoe UI", 10)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            right_buttons, text="▶ Install Selected", command=start,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
            text_color=COLOR_FG_BRIGHT, font=("Segoe UI", 11, "bold"),
            width=150, height=30
        ).pack(side="left")

        # Search filter
        def on_search(*_):
            q = (search_var.get() or '').lower().strip()
            for frame, text in item_rows:
                if not q or q in text:
                    frame.grid()
                else:
                    frame.grid_remove()
        search_var.trace_add('write', on_search)


    def _bind_timeline_scroll(self):
        # Mouse wheel (Windows/Mac) and Linux scroll events
        self.root.bind_all('<MouseWheel>', self._timeline_scroll_wheel)
        self.root.bind_all('<Shift-MouseWheel>', self._timeline_scroll_wheel)
        self.root.bind_all('<Button-4>', lambda e: self.timeline_canvas.xview_scroll(-3, 'units'))
        self.root.bind_all('<Button-5>', lambda e: self.timeline_canvas.xview_scroll(3, 'units'))

    def _unbind_timeline_scroll(self):
        self.root.unbind_all('<MouseWheel>')
        self.root.unbind_all('<Shift-MouseWheel>')
        self.root.unbind_all('<Button-4>')
        self.root.unbind_all('<Button-5>')

    def _timeline_scroll_wheel(self, event):
        # Normalize delta; horizontal scroll if Shift held or always for this canvas
        delta = event.delta
        if delta == 0:
            return
        direction = -1 if delta > 0 else 1
        self.timeline_canvas.xview_scroll(direction * 3, 'units')

    def _timeline_drag_start(self, event):
        self._drag_last_x = event.x

    def _timeline_drag_move(self, event):
        if self._drag_last_x is None:
            return
        dx = self._drag_last_x - event.x
        if dx != 0:
            self.timeline_canvas.xview_scroll(int(dx / 10), 'units')
            self._drag_last_x = event.x


def is_ctk_available() -> bool:
    """Check if CustomTkinter is available"""
    return CTK_AVAILABLE

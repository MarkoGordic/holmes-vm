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
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Step info
        step_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        step_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        step_frame.grid_columnconfigure(1, weight=1)
        
        self.step_label = ctk.CTkLabel(
            step_frame,
            text="Step 0/0",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_ACCENT
        )
        self.step_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        self.substatus_label = ctk.CTkLabel(
            step_frame,
            text="Preparing...",
            font=("Segoe UI", 12),
            text_color=COLOR_FG
        )
        self.substatus_label.grid(row=0, column=1, sticky="w")
        
        # Progress bar (modern, deterministic)
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=25,
            progress_color=COLOR_ACCENT,
            fg_color=COLOR_BG_TERTIARY
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.progress_bar.set(0)
        
        # Progress percentage
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_ACCENT_LIGHT
        )
        self.progress_label.grid(row=2, column=0)
        
        # === Log Section with Scrollable Frame ===
        log_container = ctk.CTkFrame(main_frame, fg_color=COLOR_BG)
        log_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 10))
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
        footer_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
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
            text_color=COLOR_WARN,
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
    
    def enqueue(self, item: tuple):
        """Add item to processing queue"""
        self.queue.put(item)
    
    def _append_log(self, level: str, line: str):
        """Append log message to textbox"""
        if not self._filters.get(level, True):
            return
        
        self.log_textbox.configure(state="normal")
        
        # Color-code based on level
        color_map = {
            'info': COLOR_INFO,
            'warn': COLOR_WARN,
            'error': COLOR_ERROR,
            'success': COLOR_SUCCESS,
            'verbose': COLOR_MUTED_DARK
        }
        
        color = color_map.get(level, COLOR_FG)
        
        # Insert with color (CustomTkinter doesn't support tags like regular Text widget)
        # So we just insert normally - the monospace font helps readability
        self.log_textbox.insert("end", line)
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
        """Animate progress to target (for now, just set it)"""
        self.set_progress(target)
    
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
        # Use proper Python ternary expression
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
        """Show component selection dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Tools")
        dialog.geometry("900x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configure grid
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color=COLOR_BG_SECONDARY, height=100)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            header,
            text="🔍 Choose Your Installation Tools",
            font=("Segoe UI", 20, "bold"),
            text_color=COLOR_ACCENT_LIGHT
        )
        title.grid(row=0, column=0, pady=(20, 5))
        
        subtitle = ctk.CTkLabel(
            header,
            text="Select forensics tools to install • You can add more later",
            font=("Segoe UI", 11),
            text_color=COLOR_MUTED
        )
        subtitle.grid(row=1, column=0, pady=(0, 15))
        
        # Scrollable frame for selection
        scroll_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color=COLOR_BG,
            label_text="",
            label_fg_color=COLOR_BG
        )
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10))
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Build selection UI
        vars_map = {}
        for cat_idx, cat in enumerate(registry):
            # Category header
            cat_frame = ctk.CTkFrame(scroll_frame, fg_color=COLOR_BG_SECONDARY)
            cat_frame.grid(row=cat_idx*2, column=0, sticky="ew", pady=(10, 5), padx=5)
            cat_frame.grid_columnconfigure(0, weight=1)
            
            cat_label = ctk.CTkLabel(
                cat_frame,
                text=cat['name'],
                font=("Segoe UI", 14, "bold"),
                text_color=COLOR_FG_BRIGHT,
                anchor="w"
            )
            cat_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))
            
            if cat.get('description'):
                desc_label = ctk.CTkLabel(
                    cat_frame,
                    text=cat['description'],
                    font=("Segoe UI", 10),
                    text_color=COLOR_MUTED,
                    anchor="w"
                )
                desc_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))
            
            # Items
            items_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            items_frame.grid(row=cat_idx*2+1, column=0, sticky="ew", padx=10, pady=(0, 5))
            items_frame.grid_columnconfigure(0, weight=1)
            
            for item_idx, item in enumerate(cat['items']):
                default_selected = (
                    preselected_ids is None and item.get('default', True)
                ) or (
                    preselected_ids and item['id'] in preselected_ids
                )
                
                var = ctk.BooleanVar(value=default_selected)
                vars_map[item['id']] = var
                
                item_frame = ctk.CTkFrame(items_frame, fg_color="transparent")
                item_frame.grid(row=item_idx, column=0, sticky="ew", pady=3)
                item_frame.grid_columnconfigure(1, weight=1)
                
                cb = ctk.CTkCheckBox(
                    item_frame,
                    text=item['name'],
                    variable=var,
                    fg_color=COLOR_ACCENT,
                    text_color=COLOR_FG,
                    font=("Segoe UI", 11)
                )
                cb.grid(row=0, column=0, sticky="w", padx=10)
                
                if item.get('description'):
                    desc = ctk.CTkLabel(
                        item_frame,
                        text=f"• {item['description']}",
                        font=("Segoe UI", 9),
                        text_color=COLOR_MUTED,
                        anchor="w"
                    )
                    desc.grid(row=0, column=1, sticky="w", padx=15)
        
        # Footer with buttons
        footer = ctk.CTkFrame(dialog, fg_color=COLOR_BG_SECONDARY, height=80)
        footer.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        footer.grid_columnconfigure(1, weight=1)
        
        # Left buttons
        left_buttons = ctk.CTkFrame(footer, fg_color="transparent")
        left_buttons.grid(row=0, column=0, sticky="w", padx=20, pady=20)
        
        def select_all():
            for v in vars_map.values():
                v.set(True)
        
        def deselect_all():
            for v in vars_map.values():
                v.set(False)
        
        ctk.CTkButton(
            left_buttons, text="☑ Select All", command=select_all,
            fg_color=COLOR_BG_TERTIARY, hover_color=COLOR_MUTED_DARK,
            text_color=COLOR_INFO, width=120, height=35
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            left_buttons, text="☐ Deselect All", command=deselect_all,
            fg_color=COLOR_BG_TERTIARY, hover_color=COLOR_MUTED_DARK,
            text_color=COLOR_WARN, width=120, height=35
        ).pack(side="left")
        
        # Right buttons
        right_buttons = ctk.CTkFrame(footer, fg_color="transparent")
        right_buttons.grid(row=0, column=1, sticky="e", padx=20, pady=20)
        
        def cancel():
            dialog.destroy()
            self.root.destroy()
        
        def start():
            selected = [k for k, v in vars_map.items() if v.get()]
            dialog.destroy()
            on_start(selected)
        
        ctk.CTkButton(
            right_buttons, text="✗ Cancel", command=cancel,
            fg_color=COLOR_BG_TERTIARY, hover_color=COLOR_MUTED_DARK,
            text_color=COLOR_MUTED, width=100, height=35
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            right_buttons, text="🔍 Start Installation", command=start,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_DARK,
            text_color=COLOR_FG_BRIGHT, font=("Segoe UI", 12, "bold"),
            width=180, height=35
        ).pack(side="left")


def is_ctk_available() -> bool:
    """Check if CustomTkinter is available"""
    return CTK_AVAILABLE

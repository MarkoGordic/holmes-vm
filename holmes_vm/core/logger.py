#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging utilities for Holmes VM setup
Enhanced with Rich console support and ANSI-colored plain console fallback
to match the UI palette.
"""

import os
import sys
import ctypes
import threading
from datetime import datetime
from typing import Optional, Any


class Logger:
    """Thread-safe logger with UI integration support (GUI and Rich console)"""
    
    def __init__(self, log_file: str, ui: Optional[Any] = None, rich_console: Optional[Any] = None):
        self.log_file = log_file
        self.ui = ui  # GUI UI object
        self.rich_console = rich_console  # Rich console UI object
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self._lock = threading.Lock()
        self.current_step = None  # Optional context injected by runner
        # Use a clearly named flag for verbosity to avoid name clashes with methods
        self._verbose_enabled = True
        # Prepare ANSI color palette for plain console fallback
        self._ansi_enabled = self._detect_ansi_support()
        self._palette = self._build_palette() if self._ansi_enabled else {
            'INFO': '', 'WARN': '', 'ERROR': '', 'SUCCESS': '', 'VERBOSE': '',
            'DIM': '', 'BOLD': '', 'RESET': '', 'MUTED': ''
        }

    @staticmethod
    def _hex_to_ansi_fg(hex_code: str) -> str:
        """Convert #RRGGBB to ANSI 24-bit foreground sequence."""
        try:
            hex_code = hex_code.lstrip('#')
            if len(hex_code) != 6:
                return ''
            r = int(hex_code[0:2], 16)
            g = int(hex_code[2:4], 16)
            b = int(hex_code[4:6], 16)
            return f"\033[38;2;{r};{g};{b}m"
        except Exception:
            return ''

    def _build_palette(self) -> dict:
        """Build ANSI palette based on UI theme colors."""
        try:
            from holmes_vm.ui import colors as ui
            return {
                'INFO': self._hex_to_ansi_fg(ui.COLOR_INFO),
                'WARN': self._hex_to_ansi_fg(ui.COLOR_WARN),
                'ERROR': self._hex_to_ansi_fg(ui.COLOR_ERROR),
                'SUCCESS': self._hex_to_ansi_fg(ui.COLOR_SUCCESS),
                'VERBOSE': self._hex_to_ansi_fg(ui.COLOR_MUTED_DARK),
                'MUTED': self._hex_to_ansi_fg(ui.COLOR_MUTED),
                'DIM': '\033[2m',
                'BOLD': '\033[1m',
                'RESET': '\033[0m',
            }
        except Exception:
            # Fallback to simple green/yellow/red/blue if UI colors unavailable
            return {
                'INFO': '\033[36m',  # cyan
                'WARN': '\033[33m',  # yellow
                'ERROR': '\033[31m', # red
                'SUCCESS': '\033[32m',
                'VERBOSE': '\033[90m',
                'MUTED': '\033[90m',
                'DIM': '\033[2m',
                'BOLD': '\033[1m',
                'RESET': '\033[0m',
            }

    @staticmethod
    def _enable_vt_on_windows() -> bool:
        """Try enabling VT processing on Windows consoles."""
        try:
            if os.name != 'nt':
                return True
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            for handle in (-11, -12):  # STD_OUTPUT_HANDLE, STD_ERROR_HANDLE
                h = kernel32.GetStdHandle(handle)
                if h in (0, -1):
                    continue
                mode = ctypes.c_uint32()
                if not kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                    continue
                new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(h, new_mode)
            return True
        except Exception:
            return False

    def _detect_ansi_support(self) -> bool:
        """Detect if ANSI colors should be used in plain console fallback."""
        if not sys.stdout.isatty():
            return False
        if os.name != 'nt':
            return True
        # Windows: try to enable VT
        return self._enable_vt_on_windows()

    def _write_file(self, line: str):
        """Write log line to file"""
        with self._lock:
            try:
                with open(self.log_file, 'a', encoding='utf-8', errors='ignore') as f:
                    f.write(line)
            except Exception:
                pass

    def log(self, level: str, msg: str, verbose: bool = False):
        """Log a message with specified level"""
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        ctx = f"[{self.current_step}]" if self.current_step else ""
        line = f"[{ts}][{level.upper()}]{ctx} {msg}\n"
        
        # Always write to file
        self._write_file(line)
        
        # Send to GUI if available
        if self.ui:
            self.ui.enqueue(('log', level.lower(), line))
        
        # Send to Rich console if available and not in GUI mode
        if self.rich_console and not self.ui:
            if verbose and not self._verbose_enabled:
                return  # Skip verbose messages if verbosity is off
            
            if verbose:
                # Verbose/debug path
                if hasattr(self.rich_console, 'log_verbose'):
                    self.rich_console.log_verbose(msg)
                else:
                    self.rich_console.log_info(msg)
            elif level.upper() == 'INFO':
                self.rich_console.log_info(msg)
            elif level.upper() == 'SUCCESS':
                self.rich_console.log_success(msg)
            elif level.upper() == 'WARN':
                self.rich_console.log_warning(msg)
            elif level.upper() == 'ERROR':
                self.rich_console.log_error(msg)
            else:
                self.rich_console.log_info(msg)
        elif not self.ui and not self.rich_console:
            # Fallback to plain console with optional ANSI colors
            if self._ansi_enabled:
                pal = self._palette
                lvl = level.upper()
                lvl_color = pal.get(lvl, pal['INFO'])
                ts_end = line.find(']') + 1 if ']' in line else 0
                ts_part = line[:ts_end]
                rest = line[ts_end:]
                # Color timestamp dim, level token colored, rest muted for VERBOSE
                colored = f"{pal['DIM']}{ts_part}{pal['RESET']}"
                # Replace first [LEVEL] occurrence with colored version
                if f"[{lvl}]" in rest:
                    rest = rest.replace(f"[{lvl}]", f"[{lvl_color}{lvl}{pal['RESET']}]")
                if lvl == 'VERBOSE':
                    rest = f"{pal['VERBOSE']}{rest}{pal['RESET']}"
                elif lvl in ('WARN', 'ERROR', 'SUCCESS', 'INFO'):
                    rest = f"{lvl_color}{rest}{pal['RESET']}"
                print(colored + rest, end='')
            else:
                print(line, end='')

    def info(self, msg: str, verbose: bool = False):
        """Log info message"""
        self.log('INFO', msg, verbose)

    def warn(self, msg: str, verbose: bool = False):
        """Log warning message"""
        self.log('WARN', msg, verbose)

    def error(self, msg: str, verbose: bool = False):
        """Log error message"""
        self.log('ERROR', msg, verbose)

    def success(self, msg: str, verbose: bool = False):
        """Log success message"""
        self.log('SUCCESS', msg, verbose)
    
    def debug(self, msg: str):
        """Log verbose/debug message"""
        self.log('VERBOSE', msg, verbose=True)
    
    def set_verbose(self, enabled: bool):
        """Enable or disable verbose logging"""
        self._verbose_enabled = enabled


def get_default_log_dir() -> str:
    """Get default log directory path in a cross-platform way"""
    # Prefer a sensible default per platform. On Windows, respect ProgramData.
    if os.name == 'nt':
        base = os.environ.get('ProgramData', r'C:\\ProgramData')
        return os.path.join(base, 'HolmesVM', 'Logs')
    # On POSIX (developer machines), store under user home
    return os.path.join(os.path.expanduser('~'), '.holmesvm', 'logs')


def create_logger(log_dir: Optional[str] = None, ui: Optional[Any] = None, rich_console: Optional[Any] = None) -> Logger:
    """Create a new logger instance"""
    if log_dir is None:
        log_dir = get_default_log_dir()
    
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(
        log_dir,
        f"HolmesVM-setup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    )
    
    return Logger(log_file, ui, rich_console)


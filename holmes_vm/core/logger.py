#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging utilities for Holmes VM setup
Enhanced with Rich console support for beautiful terminal output
"""

import os
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
            # Fallback to plain console
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


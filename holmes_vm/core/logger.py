#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging utilities for Holmes VM setup
"""

import os
import threading
from datetime import datetime
from typing import Optional, Any


class Logger:
    """Thread-safe logger with UI integration support"""
    
    def __init__(self, log_file: str, ui: Optional[Any] = None):
        self.log_file = log_file
        self.ui = ui
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self._lock = threading.Lock()
        self.current_step = None  # Optional context injected by runner

    def _write_file(self, line: str):
        """Write log line to file"""
        with self._lock:
            try:
                with open(self.log_file, 'a', encoding='utf-8', errors='ignore') as f:
                    f.write(line)
            except Exception:
                pass

    def log(self, level: str, msg: str):
        """Log a message with specified level"""
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        ctx = f"[{self.current_step}]" if self.current_step else ""
        line = f"[{ts}][{level.upper()}]{ctx} {msg}\n"
        
        self._write_file(line)
        
        if self.ui:
            self.ui.enqueue(('log', level.lower(), line))
        
        # Also echo to console
        print(line, end='')

    def info(self, msg: str):
        """Log info message"""
        self.log('INFO', msg)

    def warn(self, msg: str):
        """Log warning message"""
        self.log('WARN', msg)

    def error(self, msg: str):
        """Log error message"""
        self.log('ERROR', msg)

    def success(self, msg: str):
        """Log success message"""
        self.log('SUCCESS', msg)


def get_default_log_dir() -> str:
    """Get default log directory path"""
    return os.path.join(
        os.environ.get('ProgramData', 'C:/ProgramData'),
        'HolmesVM',
        'Logs'
    )


def create_logger(log_dir: Optional[str] = None, ui: Optional[Any] = None) -> Logger:
    """Create a new logger instance"""
    if log_dir is None:
        log_dir = get_default_log_dir()
    
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(
        log_dir,
        f"HolmesVM-setup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    )
    
    return Logger(log_file, ui)

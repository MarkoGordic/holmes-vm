#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System utilities for Holmes VM setup
"""

import sys
import ctypes
import subprocess
import os


def is_admin() -> bool:
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def is_windows() -> bool:
    """Check if running on Windows"""
    return sys.platform == 'win32'


def run_powershell(ps_code: str, cwd: str = None, timeout: int = None) -> subprocess.CompletedProcess:
    """Run PowerShell code and return result"""
    cmd = [
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-Command', f"$ErrorActionPreference='Stop'; {ps_code}"
    ]
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


def import_common_module_and(ps_inner: str, module_path: str) -> str:
    """Generate PowerShell code to import common module and run command"""
    mod = module_path.replace('`', '``').replace("'", "''")
    return f"Import-Module '{mod}' -Force -DisableNameChecking; {ps_inner}"


def dot_source_and(ps1_path: str, call: str) -> str:
    """Generate PowerShell code to dot-source script and call function"""
    p = ps1_path.replace('`', '``').replace("'", "''")
    return f". '{p}'; {call}"


def check_network(urls: list = None) -> bool:
    """Check network connectivity"""
    import urllib.request
    
    if urls is None:
        urls = ['https://www.google.com/generate_204', 'https://github.com']
    
    ok = 0
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=7) as resp:  # nosec B310
                if 200 <= resp.status < 400:
                    ok += 1
        except Exception:
            pass
    
    return ok > 0

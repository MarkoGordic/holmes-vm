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


def run_powershell(ps_code: str, cwd: str = None, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run PowerShell code and return result.

    Args:
        ps_code: PowerShell code to execute.
        cwd: Working directory for the subprocess.
        timeout: Max seconds to wait (default 600 = 10 min). Pass None to wait indefinitely.

    Returns:
        CompletedProcess with stdout/stderr.
    """
    if not is_windows():
        # Return a synthetic failure on non-Windows so callers can handle gracefully
        return subprocess.CompletedProcess(
            args=[], returncode=1,
            stdout='', stderr='PowerShell is not available on this platform'
        )
    cmd = [
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-Command', f"$ErrorActionPreference='Stop'; {ps_code}"
    ]
    try:
        return subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=cmd, returncode=1,
            stdout='', stderr=f'PowerShell command timed out after {timeout}s'
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=cmd, returncode=1,
            stdout='', stderr='powershell.exe not found on PATH'
        )


def run_powershell_streamed(ps_code: str, logger=None, cwd: str = None, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run PowerShell and stream stdout/stderr to the logger line-by-line.

    This gives real-time feedback for long-running operations like downloads
    and installations, instead of buffering all output until completion.

    Returns a CompletedProcess with combined stdout for compatibility.
    """
    if not is_windows():
        return subprocess.CompletedProcess(
            args=[], returncode=1,
            stdout='', stderr='PowerShell is not available on this platform'
        )
    cmd = [
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-Command', f"$ErrorActionPreference='Stop'; {ps_code}"
    ]
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=cmd, returncode=1,
            stdout='', stderr='powershell.exe not found on PATH'
        )

    stdout_lines = []
    stderr_lines = []

    def _read_stream(stream, lines_list, level):
        for line in stream:
            stripped = line.rstrip('\n\r')
            if not stripped:
                continue
            lines_list.append(stripped)
            if logger:
                logger.info(f'  {stripped}', verbose=True)

    import threading as _threading
    t_out = _threading.Thread(target=_read_stream, args=(proc.stdout, stdout_lines, 'INFO'), daemon=True)
    t_err = _threading.Thread(target=_read_stream, args=(proc.stderr, stderr_lines, 'WARN'), daemon=True)
    t_out.start()
    t_err.start()

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        return subprocess.CompletedProcess(
            args=cmd, returncode=1,
            stdout='\n'.join(stdout_lines),
            stderr=f'PowerShell command timed out after {timeout}s'
        )

    t_out.join(timeout=5)
    t_err.join(timeout=5)

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=proc.returncode,
        stdout='\n'.join(stdout_lines),
        stderr='\n'.join(stderr_lines)
    )


def import_common_module_and(ps_inner: str, module_path: str) -> str:
    """Generate PowerShell code to import common module and run command"""
    mod = module_path.replace('`', '``').replace("'", "''")
    return f"Import-Module '{mod}' -Force -DisableNameChecking; {ps_inner}"


def dot_source_and(ps1_path: str, call: str) -> str:
    """Generate PowerShell code to dot-source script and call function"""
    p = ps1_path.replace('`', '``').replace("'", "''")
    return f". '{p}'; {call}"



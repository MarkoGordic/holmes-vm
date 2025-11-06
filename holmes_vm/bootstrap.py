#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Holmes VM Bootstrap Script
This script sets up Python environment and dependencies for Holmes VM.
Run this first on a fresh Windows installation.
Enhanced with Sherlock Holmes theme.
"""

import os
import sys
import subprocess
import urllib.request
import tempfile
import ctypes
from pathlib import Path


# ANSI color codes for terminal styling (with ability to disable on unsupported consoles)
class Colors:
    BROWN = '\033[38;5;138m'     # Victorian brown
    GOLD = '\033[38;5;179m'      # Golden brown
    GREEN = '\033[38;5;108m'     # Muted green
    RED = '\033[38;5;167m'       # Muted red
    GRAY = '\033[38;5;248m'      # Warm gray
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

    @classmethod
    def disable(cls):
        cls.BROWN = ''
        cls.GOLD = ''
        cls.GREEN = ''
        cls.RED = ''
        cls.GRAY = ''
        cls.BOLD = ''
        cls.DIM = ''
        cls.RESET = ''


def _hex_to_ansi_fg(hex_code: str) -> str:
    """Convert #RRGGBB to ANSI 24-bit foreground escape sequence."""
    hex_code = hex_code.lstrip('#')
    if len(hex_code) != 6:
        return ''
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


def _apply_ui_palette():
    """Map UI hex colors to ANSI sequences for console output."""
    try:
        from holmes_vm.ui import colors as ui
        Colors.BROWN = _hex_to_ansi_fg(ui.COLOR_ACCENT)       # Accent teal
        Colors.GOLD = _hex_to_ansi_fg(ui.COLOR_WARN)          # Muted amber
        Colors.GREEN = _hex_to_ansi_fg(ui.COLOR_SUCCESS)      # Success teal-green
        Colors.RED = _hex_to_ansi_fg(ui.COLOR_ERROR)          # Soft red
        Colors.GRAY = _hex_to_ansi_fg(ui.COLOR_MUTED)         # Blue-gray
        Colors.BOLD = '\033[1m'
        Colors.DIM = '\033[2m'
        Colors.RESET = '\033[0m'
    except Exception:
        # If palette import fails, keep existing defaults (or disabled state)
        pass


def get_banner() -> str:
    """Build the banner string using current Colors (allows disabling later)."""
    return (
        f"{Colors.BROWN}{Colors.BOLD}\n"
        "╔══════════════════════════════════════════════════════════════════════════╗\n"
        "║                                                                          ║\n"
        "║   🔍 SHERLOCK HOLMES • DIGITAL FORENSICS VM BOOTSTRAP                   ║\n"
        "║                                                                          ║\n"
        "║      \"It is a capital mistake to theorize before one has data.\"         ║\n"
        "║                                          - A Scandal in Bohemia          ║\n"
        "║                                                                          ║\n"
        "╚══════════════════════════════════════════════════════════════════════════╝\n"
        f"{Colors.RESET}\n"
    )

def _try_enable_ansi_on_windows() -> bool:
    """Attempt to enable ANSI escape processing on Windows consoles.

    Returns True if either not on Windows or enabling succeeded.
    """
    try:
        if os.name != 'nt':
            return True
        # Windows 10+ can support VT with this flag
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12

        for handle in (STD_OUTPUT_HANDLE, STD_ERROR_HANDLE):
            h = kernel32.GetStdHandle(handle)
            if h == 0 or h == -1:
                continue
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                continue
            new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(h, new_mode)
        return True
    except Exception:
        return False

def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BROWN}{Colors.BOLD}{'═' * 76}")
    print(f"  {text}")
    print(f"{'═' * 76}{Colors.RESET}\n")


def print_step(step_num, total, text):
    """Print a step indicator"""
    print(f"{Colors.GRAY}{Colors.BOLD}[{step_num}/{total}]{Colors.RESET} {Colors.BROWN}🔍 {text}...{Colors.RESET}")


def print_success(text):
    """Print success message"""
    print(f"  {Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """Print error message"""
    print(f"  {Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    """Print info message"""
    print(f"  {Colors.GRAY}→ {text}{Colors.RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"  {Colors.GOLD}⚠ {text}{Colors.RESET}")


def check_python_version():
    """Check if Python version is adequate"""
    print_step(1, 5, "Checking Python version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error(f"Python {version.major}.{version.minor} is too old")
        print_info("Holmes VM requires Python 3.7 or newer")
        print_info("Download from: https://www.python.org/downloads/")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_tkinter():
    """Check if tkinter is available"""
    print_step(2, 5, "Checking Tkinter (for GUI)")
    
    try:
        import tkinter
        print_success("Tkinter is available")
        return True
    except ImportError:
        print_error("Tkinter not available")
        print_info("GUI mode will not be available")
        print_info("You can still use --no-gui flag")
        return False


def upgrade_pip():
    """Upgrade pip to latest version"""
    print_step(3, 5, "Upgrading pip")
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("pip upgraded to latest version")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to upgrade pip: {e}")
        return False


def install_dependencies():
    """Install required Python packages"""
    print_step(4, 5, "Installing dependencies")
    
    # Core dependencies including Rich for beautiful UI and CustomTkinter for modern GUI
    dependencies = [
        'setuptools',
        'wheel',
        'rich>=13.7.0',        # Beautiful terminal UI
        'customtkinter>=5.2.0',  # Modern tkinter wrapper with better widgets
    ]
    
    print_info(f"Installing: {', '.join(dependencies)}")
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade'] + dependencies,
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Dependencies installed (Rich + CustomTkinter for modern UI)")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def verify_installation():
    """Verify the installation is ready"""
    print_step(5, 5, "Verifying installation")

    pkg_dir = Path(__file__).resolve().parent
    repo_root = pkg_dir.parent

    # Check if setup.py exists (module file inside package)
    setup_path = pkg_dir / 'setup.py'
    if not setup_path.exists():
        print_error("holmes_vm/setup.py not found")
        print_info("Ensure you cloned the repository correctly")
        return False

    # Check if config exists at repo root
    config_path = repo_root / 'config' / 'tools.json'
    if not config_path.exists():
        print_error("config/tools.json not found at repository root")
        return False

    # Check if PowerShell module exists under scripts/windows at repo root
    module_path = repo_root / 'scripts' / 'windows' / 'Holmes.Common.psm1'
    if not module_path.exists():
        print_error("scripts/windows/Holmes.Common.psm1 not found at repository root")
        return False

    print_success("Installation verified")
    print_success("All required files are present")
    return True


def check_admin_rights():
    """Check and warn about admin rights"""
    if not is_admin():
        print(f"\n{Colors.GOLD}{Colors.BOLD}{'!' * 76}")
        print("  ⚠  WARNING: Not running as Administrator")
        print("  Holmes VM requires Administrator privileges to install tools")
        print("  Please run this script (and setup.py) as Administrator")
        print(f"{'!' * 76}{Colors.RESET}\n")
        return False
    else:
        print_success("Running with Administrator privileges")
        return True


def main():
    """Main bootstrap function"""
    # Configure color support: try to enable ANSI on Windows; if it fails, strip colors
    ansi_ok = _try_enable_ansi_on_windows()
    if sys.stdout.isatty() and ansi_ok:
        _apply_ui_palette()
    else:
        Colors.disable()

    # Print banner
    print(get_banner())
    
    print_header("Holmes VM Bootstrap Script")
    print(f"{Colors.DIM}This script prepares your system to run Holmes VM setup.")
    print(f"Make sure you're running this as Administrator!{Colors.RESET}\n")
    
    # Check admin rights
    is_admin_user = check_admin_rights()
    
    # Run all checks and setup steps
    steps_passed = 0
    total_steps = 5
    
    if check_python_version():
        steps_passed += 1
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Python version check failed. Please upgrade Python.{Colors.RESET}")
        sys.exit(1)
    
    if check_tkinter():
        steps_passed += 1
    else:
        print_info("Continuing without GUI support...")
        steps_passed += 1  # Not critical
    
    if upgrade_pip():
        steps_passed += 1
    else:
        print_warning("pip upgrade failed, but continuing...")
        steps_passed += 1  # Not critical
    
    if install_dependencies():
        steps_passed += 1
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Dependency installation failed.{Colors.RESET}")
        sys.exit(1)
    
    if verify_installation():
        steps_passed += 1
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Installation verification failed.{Colors.RESET}")
        sys.exit(1)
    
    # Final summary
    print_header("Bootstrap Complete!")
    print(f"{Colors.GREEN}{Colors.BOLD}✓ All {steps_passed}/{total_steps} steps completed successfully!{Colors.RESET}\n")
    
    if is_admin_user:
        print(f"{Colors.BROWN}You can now run Holmes VM setup:{Colors.RESET}")
        print(f"  {Colors.BOLD}python holmes_vm/setup.py{Colors.RESET}")
    else:
        print(f"{Colors.GOLD}⚠  IMPORTANT: Run setup as Administrator:{Colors.RESET}")
        print("  1. Open Command Prompt or PowerShell as Administrator")
        print("  2. Navigate to this directory")
        print(f"  3. Run: {Colors.BOLD}python holmes_vm/setup.py{Colors.RESET}")
    
    print(f"\n{Colors.DIM}Other options:{Colors.RESET}")
    print(f"  {Colors.BROWN}python holmes_vm/setup.py --no-gui{Colors.RESET}       # Console mode with Rich UI")
    print(f"  {Colors.BROWN}python holmes_vm/setup.py --what-if{Colors.RESET}      # Test mode")
    print(f"  {Colors.BROWN}python holmes_vm/setup.py --help{Colors.RESET}         # Show all options")
    
    print(f"\n{Colors.DIM}For more information, see README.md{Colors.RESET}")
    print(f"{Colors.BROWN}{'═' * 76}{Colors.RESET}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GOLD}⚠  Bootstrap interrupted by user.{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}{Colors.BOLD}❌ Bootstrap failed with error: {e}{Colors.RESET}")
        sys.exit(1)

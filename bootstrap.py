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


# ANSI color codes for terminal styling
class Colors:
    BROWN = '\033[38;5;138m'     # Victorian brown
    GOLD = '\033[38;5;179m'      # Golden brown
    GREEN = '\033[38;5;108m'     # Muted green
    RED = '\033[38;5;167m'       # Muted red
    GRAY = '\033[38;5;248m'      # Warm gray
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


# Sherlock Holmes banner
BANNER = f"""{Colors.BROWN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🔍 SHERLOCK HOLMES • DIGITAL FORENSICS VM BOOTSTRAP                   ║
║                                                                          ║
║      "It is a capital mistake to theorize before one has data."         ║
║                                          - A Scandal in Bohemia          ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""

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
    
    # Check if setup.py exists
    setup_path = Path(__file__).parent / 'setup.py'
    if not setup_path.exists():
        print_error("setup.py not found")
        print_info("Make sure you're in the holmes-vm directory")
        return False
    
    # Check if config exists
    config_path = Path(__file__).parent / 'config' / 'tools.json'
    if not config_path.exists():
        print_error("config/tools.json not found")
        return False
    
    # Check if PowerShell module exists
    module_path = Path(__file__).parent / 'modules' / 'Holmes.Common.psm1'
    if not module_path.exists():
        print_error("modules/Holmes.Common.psm1 not found")
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
    # Print banner
    print(BANNER)
    
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
        print(f"  {Colors.BOLD}python setup.py{Colors.RESET}")
    else:
        print(f"{Colors.GOLD}⚠  IMPORTANT: Run setup as Administrator:{Colors.RESET}")
        print("  1. Open Command Prompt or PowerShell as Administrator")
        print("  2. Navigate to this directory")
        print(f"  3. Run: {Colors.BOLD}python setup.py{Colors.RESET}")
    
    print(f"\n{Colors.DIM}Other options:{Colors.RESET}")
    print(f"  {Colors.BROWN}python setup.py --no-gui{Colors.RESET}       # Console mode with Rich UI")
    print(f"  {Colors.BROWN}python setup.py --what-if{Colors.RESET}      # Test mode")
    print(f"  {Colors.BROWN}python setup.py --help{Colors.RESET}         # Show all options")
    
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

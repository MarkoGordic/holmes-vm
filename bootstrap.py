#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Holmes VM Bootstrap Script
This script sets up Python environment and dependencies for Holmes VM.
Run this first on a fresh Windows installation.
"""

import os
import sys
import subprocess
import urllib.request
import tempfile
import ctypes
from pathlib import Path


def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step_num, total, text):
    """Print a step indicator"""
    print(f"[{step_num}/{total}] {text}...")


def print_success(text):
    """Print success message"""
    print(f"✓ {text}")


def print_error(text):
    """Print error message"""
    print(f"✗ {text}")


def print_info(text):
    """Print info message"""
    print(f"  → {text}")


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
    
    # Core dependencies (minimal, since we mainly use stdlib and PowerShell)
    dependencies = [
        'setuptools',
        'wheel',
    ]
    
    print_info(f"Installing: {', '.join(dependencies)}")
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade'] + dependencies,
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Dependencies installed")
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
        print("\n" + "!" * 70)
        print("  WARNING: Not running as Administrator")
        print("  Holmes VM requires Administrator privileges to install tools")
        print("  Please run this script (and setup.py) as Administrator")
        print("!" * 70 + "\n")
        return False
    else:
        print_success("Running with Administrator privileges")
        return True


def main():
    """Main bootstrap function"""
    print_header("Holmes VM Bootstrap Script")
    print("This script prepares your system to run Holmes VM setup.")
    print("Make sure you're running this as Administrator!\n")
    
    # Check admin rights
    is_admin_user = check_admin_rights()
    
    # Run all checks and setup steps
    steps_passed = 0
    total_steps = 5
    
    if check_python_version():
        steps_passed += 1
    else:
        print("\n❌ Python version check failed. Please upgrade Python.")
        sys.exit(1)
    
    if check_tkinter():
        steps_passed += 1
    else:
        print_info("Continuing without GUI support...")
        steps_passed += 1  # Not critical
    
    if upgrade_pip():
        steps_passed += 1
    else:
        print("\n⚠️  pip upgrade failed, but continuing...")
        steps_passed += 1  # Not critical
    
    if install_dependencies():
        steps_passed += 1
    else:
        print("\n❌ Dependency installation failed.")
        sys.exit(1)
    
    if verify_installation():
        steps_passed += 1
    else:
        print("\n❌ Installation verification failed.")
        sys.exit(1)
    
    # Final summary
    print_header("Bootstrap Complete!")
    print(f"✓ All {steps_passed}/{total_steps} steps completed successfully!\n")
    
    if is_admin_user:
        print("You can now run Holmes VM setup:")
        print("  python setup.py")
    else:
        print("⚠️  IMPORTANT: Run setup as Administrator:")
        print("  1. Open Command Prompt or PowerShell as Administrator")
        print("  2. Navigate to this directory")
        print("  3. Run: python setup.py")
    
    print("\nOther options:")
    print("  python setup.py --no-gui       # Console mode")
    print("  python setup.py --what-if      # Test mode")
    print("  python setup.py --help         # Show all options")
    
    print("\nFor more information, see README.md")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Bootstrap interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Bootstrap failed with error: {e}")
        sys.exit(1)

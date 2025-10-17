# Holmes VM 🔍
The Blue Team's Best Friend — safe, modular, and idempotent forensics VM setup.

**Now featuring an authentic Victorian London mystery theme!**

---

## Features

✨ **Modular Architecture** - Easy to extend and maintain  
🎨 **Victorian Dark Theme** - London fog gray with warm Victorian browns  
🖥️ **Dual UI Modes** - Modern GUI or elegant Rich console interface  
⚙️ **Configurable** - JSON-based tool definitions, no code changes needed  
🔧 **Comprehensive Tooling** - All essential forensics tools in one place  
🛡️ **Safe & Idempotent** - Can be run multiple times safely  
📦 **Easy to Upgrade** - Add new tools by editing configuration  
📊 **Enhanced Progress Tracking** - Real-time updates with ETA and smooth animations  
🌙 **System Dark Mode** - Automatically sets Windows to dark theme with Victorian accent

## UI Showcase

### 🎭 Sherlock Holmes Victorian Mystery Theme

The installer features a **sophisticated dark theme** inspired by Victorian London:

- **Deep charcoal background** - Like London fog at night
- **Victorian brown accents** - Warm, professional detective aesthetic  
- **Smooth animations** - Buttery progress bars and transitions
- **Verbose logging** - Toggle detailed logs on/off
- **Mystery aesthetics** - 🔍 Magnifying glass icons and Holmes quotes
- **Grayscale elegance** - Professional forensics workspace
- **System-wide dark mode** - Applies dark theme to Windows with Victorian brown accent

### GUI Mode (Tkinter)
- **1000x700 window** - Spacious and organized
- **Animated progress bar** - Smooth transitions with dynamic speed
- **Log filtering** - Toggle Info/Warnings/Errors/Verbose
- **Enhanced component selection** - Beautiful dialog with categories
- **Time tracking** - Elapsed time and ETA
- **Hover effects** - Interactive buttons

### Rich Console Mode (New!)
- **Beautiful terminal output** - Powered by Rich library
- **ASCII art banner** - Sherlock Holmes themed
- **Animated spinners** - Live progress indicators
- **Colored panels** - Organized information display
- **Progress tracking** - Time estimates and completion status
- **Professional tables** - Summary statistics

**Try the demo:**
```bash
python demo_ui.py --full
```  

## What it installs

### Core Tools
- Chocolatey (package manager)
- Python packages (pip, setuptools, wheel, pipx, virtualenv)
- Network connectivity verification

### Applications
- Wireshark (network protocol analyzer)
- .NET 6 Desktop Runtime
- DnSpyEx (.NET debugger)
- PeStudio (malware analysis)
- WinPrefetchView (NirSoft prefetch viewer)
- Visual Studio Code
- DB Browser for SQLite
- **Brimdata Zui** (GUI for Zeek/Suricata logs)

### Forensics Bundles
- **Eric Zimmerman Tools** (EZ Tools) - comprehensive forensics toolkit
- **RegRipper** - Windows Registry forensics
- **Chainsaw** - Windows event log hunter

## Quick Start

### Prerequisites

- Windows 10/11
- Administrator privileges
- Internet connection

**Optional:**
- Rich library for enhanced console UI (auto-installed by bootstrap)

**That's it!** Python and Chocolatey will be installed automatically by the start scripts.

### Installation

#### Quick Start - Fully Automated (Recommended)

**Zero prerequisites! Just run as Administrator:**

1. **Right-click `start.bat`** → **Run as Administrator**
   
   **If the window closes immediately, try:**
   - Right-click `start-debug.bat` → Run as Administrator (verbose debug mode)
   - Or open Command Prompt as Admin and run: `start.bat`

2. **Wait for installations** (Chocolatey, Python, dependencies)
3. **Select tools** from the GUI
4. **Done!** ✨

**No manual steps required!** Everything is automatic except tool selection.

### Command Line Options

```bash
python setup.py [OPTIONS]

Options:
  --no-gui              Run in enhanced Rich console mode (no GUI window)
  --what-if             Simulate installation without making changes
  --force-reinstall     Force reinstallation of all packages
  --log-dir PATH        Custom directory for log files
```

### UI Modes

**GUI Mode (Default):**
```bash
python setup.py
```
- Modern Tkinter window with Sherlock Holmes theme
- Interactive component selection
- Smooth animations and progress tracking
- Log filtering (Info/Warnings/Errors/Verbose)

**Rich Console Mode:**
```bash
python setup.py --no-gui
```
- Beautiful terminal output with Rich library
- ASCII art banner and animations
- Colored panels and progress bars
- Professional logging

**Demo the UI:**
```bash
python demo_ui.py --full      # Full demo with simulated installation
python demo_ui.py --colors    # Show color palette
```

## Project Structure

```
holmes-vm/
├── config/
│   └── tools.json              # Tool definitions (easy to modify!)
├── holmes_vm/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── logger.py          # Enhanced logging (GUI/Rich/console)
│   │   └── orchestrator.py   # Installation orchestration
│   ├── ui/
│   │   ├── colors.py          # Sherlock Holmes theme colors
│   │   ├── window.py          # Enhanced GUI with animations
│   │   └── rich_console.py   # Rich console UI (NEW!)
│   ├── installers/
│   │   ├── base.py            # Base installer classes
│   │   ├── chocolatey.py      # Chocolatey package installer
│   │   ├── powershell.py      # PowerShell script installer
│   │   └── functions.py       # Python-based installers
│   └── utils/
│       └── system.py           # System utilities
├── modules/
│   └── Holmes.Common.psm1     # PowerShell helper functions
├── util/
│   ├── install-chainsaw.ps1   # Chainsaw installer
│   ├── install-eztools.ps1    # EZ Tools installer
│   ├── install-regripper.ps1  # RegRipper installer
│   └── install-zui.ps1        # Zui installer
├── assets/
│   └── wallpaper.jpg          # Custom wallpaper
├── requirements.txt            # Python dependencies (NEW!)
├── demo_ui.py                  # UI demonstration script (NEW!)
├── UI_UPGRADE_SUMMARY.md       # Detailed UI documentation (NEW!)
├── bootstrap.py                # Enhanced bootstrap with theme
└── setup.py                    # Main entry point
```

## Adding New Tools

Adding a new tool is easy! Just edit `config/tools.json`:

### Example: Adding a Chocolatey Package

```json
{
  "id": "newtool",
  "name": "New Tool",
  "description": "Description of the tool",
  "default": true,
  "installer_type": "chocolatey",
  "package_name": "newtool"
}
```

### Example: Adding a PowerShell Script

```json
{
  "id": "customtool",
  "name": "Custom Tool",
  "description": "Custom installer script",
  "default": true,
  "installer_type": "powershell",
  "script_path": "util/install-customtool.ps1",
  "function_name": "Install-CustomTool"
}
```

### Example: Adding Post-Install Actions

```json
{
  "id": "sometool",
  "name": "Some Tool",
  "installer_type": "chocolatey",
  "package_name": "sometool",
  "post_install": [
    {
      "type": "pin_taskbar",
      "path": "C:\\\\Program Files\\\\SomeTool\\\\sometool.exe"
    }
  ]
}
```
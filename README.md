# Holmes VM 🌌
The Blue Team's Best Friend — safe, modular, and idempotent forensics VM setup.

---

## Features

✨ **Modular Architecture** - Easy to extend and maintain  
🎨 **Modern UI** - Clean, dark-mode interface with real-time progress  
⚙️ **Configurable** - JSON-based tool definitions, no code changes needed  
🔧 **Comprehensive Tooling** - All essential forensics tools in one place  
🛡️ **Safe & Idempotent** - Can be run multiple times safely  
📦 **Easy to Upgrade** - Add new tools by editing configuration  

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

### Personalization
- Custom Holmes wallpaper
- Full dark mode theme for Windows
- Taskbar shortcuts for common tools

## Quick Start

### Prerequisites

- Windows 10/11
- Administrator privileges
- Internet connection

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

The script automatically:
1. ✅ Checks Administrator privileges
2. ✅ Installs Chocolatey (if missing)
3. ✅ Installs Python 3.14 (if missing)
4. ✅ Upgrades pip and installs dependencies
5. ✅ Runs the GUI for tool selection
6. ✅ Installs all selected tools

**Troubleshooting:**
- If `start.bat` closes immediately without output: Use `start-debug.bat` instead
- If you see errors: The window will stay open so you can read them
- If nothing happens: Make sure you're running as Administrator

**No manual steps required!** Everything is automatic except tool selection.

#### Method 2: Manual Installation (Advanced)

If you prefer to install dependencies manually or want more control:

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/MarkoGordic/holmes-vm.git
   cd holmes-vm
   ```

2. **Install Python 3.7+ manually** (if not using start.bat)

3. **Run bootstrap:**
   ```bash
   python bootstrap.py
   ```

4. **Run the installer:**
   ```bash
   python setup.py              # GUI mode
   python setup.py --no-gui     # Console mode
   ```

### Command Line Options

```bash
python setup.py [OPTIONS]

Options:
  --no-gui              Run in console mode without GUI
  --what-if             Simulate installation without making changes
  --force-reinstall     Force reinstallation of all packages
  --log-dir PATH        Custom directory for log files
```

## Project Structure

```
holmes-vm/
├── config/
│   └── tools.json              # Tool definitions (easy to modify!)
├── holmes_vm/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── logger.py          # Logging utilities
│   │   └── orchestrator.py   # Installation orchestration
│   ├── ui/
│   │   ├── colors.py          # UI color scheme
│   │   └── window.py          # Main UI window
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

## PowerShell Modules

### Holmes.Common.psm1

Shared PowerShell helpers for:
- Logging with colors (`Write-Log`)
- Chocolatey management (`Ensure-Chocolatey`, `Install-ChocoPackage`)
- Downloads with retry (`Invoke-SafeDownload`)
- PATH management (`Add-PathIfMissing`)
- Registry operations (`Set-RegistryDword`)
- **Full dark mode theme** (`Set-WindowsAppearance`) - IMPROVED!
- **Improved wallpaper setting** (`Set-Wallpaper`) - FIXED!
- Taskbar pinning (`Pin-TaskbarItem`)
- Network checks (`Test-UrlReachable`)

## Recent Improvements

✅ **Fixed Dark Mode** - Now properly applies full dark mode to all Windows components including File Explorer  
✅ **Fixed Wallpaper** - Wallpaper now correctly sets and applies with better error handling  
✅ **Fixed Zui Installation** - Improved detection and installation of Brimdata Zui  
✅ **Modular Architecture** - Complete refactoring into a clean, modular Python package  
✅ **Configuration-Driven** - All tools defined in JSON, easy to modify  
✅ **Installer Registry** - Plugin-based system for easy extensibility  
✅ **Better Logging** - Improved logging with file and UI integration  
✅ **Cleaner Code** - Separated concerns: UI, installers, config, logging, orchestration  

## Safety and Idempotency

- Checks Windows and Administrator privileges before starting
- All installations are idempotent (safe to run multiple times)
- Chocolatey packages check for existing installations
- Downloads include retry logic with TLS 1.2 support
- PATH updates are additive and non-duplicating
- `--what-if` mode for testing without changes

## Logging

All installation logs are saved to:
```
C:\ProgramData\HolmesVM\Logs\HolmesVM-setup-YYYYMMDD-HHMMSS.log
```

You can specify a custom log directory:
```bash
python setup.py --log-dir "C:\Custom\Log\Path"
```

## Troubleshooting

### "Tkinter not available"
Install Python with Tk support or use `--no-gui` flag.

### "Run as Administrator"
Right-click Command Prompt or PowerShell and select "Run as Administrator".

### Zui not installing
Check the log file for details. You may need to download manually from:
https://github.com/brimdata/zui/releases

### Wallpaper not applying
Ensure the wallpaper file exists in `assets/wallpaper.jpg` and you have write permissions to `C:\Tools\Wallpapers`.

### Dark mode not complete
Run Explorer restart manually or log out and back in to ensure all theme changes apply.

## Contributing

Contributions, tool suggestions, and feedback are welcome! 🚀

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on a clean Windows VM
5. Submit a pull request

### Adding New Installers

1. Create a new installer class in `holmes_vm/installers/`
2. Register it using the `@register_installer` decorator
3. Add the tool definition to `config/tools.json`
4. Test the installation

## License

MIT License - See LICENSE file for details.

## Credits

Created by Marko Gordic and the Holmes VM community.

Special thanks to:
- Eric Zimmerman (EZ Tools)
- NirSoft tools
- Wireshark team
- Brimdata (Zui)
- All open-source contributors

---

**For questions or issues, please open a GitHub issue.**

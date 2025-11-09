![Holmes VM](/holmes_vm/assets/github.png)

# Holmes VM

One-click setup for a Windows forensics workstation.

![Python](https://img.shields.io/badge/python-3.x-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey)
![UI](https://img.shields.io/badge/UI-GUI%20%7C%20Console-green)
![Version](https://img.shields.io/badge/version-0.3.3-blue)
![Status](https://img.shields.io/badge/status-beta-orange)

_Beta notice: current version 0.3.3 (Beta)._

---

## Features

- 🛠 Modular install: pick only the tools you need
- 🔁 Idempotent: re-run safely; existing installs are handled
- 🖥 Two modes: modern GUI or clean console (Rich)
- 📝 Logs: progress and results saved automatically
- 🎛 Optional personalization: wallpaper + dark appearance

---

## Getting Started

Requirements

- Windows 10/11
- Administrator privileges
- Internet access

Run (GUI)

1. Open an elevated terminal (Run as administrator)
2. `python holmes_vm/setup.py`
3. Choose tools and start

Console mode

- `python holmes_vm/setup.py --no-gui`

Simulation (no changes)

- `python holmes_vm/setup.py --what-if`

Options

```
python holmes_vm/setup.py [--no-gui] [--what-if] [--force-reinstall] [--log-dir PATH]
```

---

## What it installs

Core

- Chocolatey package manager
- Python tooling (pip, setuptools, wheel, pipx, virtualenv)
- Network connectivity check

Applications

- Wireshark, DnSpyEx, PeStudio, WinPrefetchView, Visual Studio Code, DB Browser for SQLite, Zui

Forensics bundles

- Eric Zimmerman Tools (EZ Tools), RegRipper, Chainsaw, Sysinternals Suite

Personalization

- Optional Holmes wallpaper and Windows dark mode

# Artemis VM (Holmes VM) 🌌
The Blue Team’s Best Friend — safe, modular, and idempotent setup.

---

## What it installs

 - Chainsaw (from GitHub releases)
 - DB Browser for SQLite (Chocolatey)
- Brimdata Zui (GUI for Zeek/Suricata logs)

## Prerequisites

- Windows host
- Elevated PowerShell session (Run as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force
cd <path-to-repo>
- `-SkipZui`
./setup.ps1
### Brimdata Zui notes

Zui is a desktop application for exploring Zeek and Suricata logs. The installer fetches the latest Windows build from GitHub releases and installs it silently. After installation, you can launch Zui from Start Menu. If you already ingest Suricata JSON, point Zui to your logs directory to explore them interactively.

```

Add `-Verbose` for details and `-WhatIf` to simulate actions.

## Options

`setup.ps1` switches:

- `-SkipWireshark`
- `-SkipDotNetDesktop`
- `-SkipDnSpyEx`
- `-SkipPeStudio`
- `-SkipEZTools`
- `-SkipRegRipper`
 - `-SkipChainsaw`
 - `-SkipSQLiteBrowser`
- `-ForceReinstall` (reinstall Chocolatey packages even if present)

Example:

```powershell
./setup.ps1 -SkipPeStudio -SkipDnSpyEx -Verbose
```

## Structure

- `modules/Holmes.Common.psm1` – shared helpers (logging, Chocolatey, downloads, PATH, shortcuts)
- `util/install-eztools.ps1` – Eric Zimmerman's tools installer
- `util/install-regripper.ps1` – RegRipper installer
- `setup.ps1` – orchestrator script

## Safety and idempotency

- Checks Windows and Administrator
- Uses `-WhatIf`/`-Verbose` where supported
- Chocolatey installs are idempotent
- Download retries, TLS 1.2 enablement
- PATH updates are additive and non-duplicating

## Contributing

Contributions, tool suggestions, and feedback are welcome! 🚀

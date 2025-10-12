# Artemis VM (Holmes VM) 🌌
The Blue Team’s Best Friend — safe, modular, and idempotent setup.

---

## What it installs

- Wireshark (Chocolatey)
- .NET 6 Desktop Runtime (Chocolatey)
- DnSpyEx (Chocolatey)
- PeStudio (Chocolatey)
- Eric Zimmerman's Tools (direct from vendor)
- RegRipper 4.0 (from GitHub)
 - Chainsaw (from GitHub releases)

## Prerequisites

- Windows host
- Elevated PowerShell session (Run as Administrator)
- Internet connectivity
- PowerShell 5.1+ (7+ recommended)

## Quick start

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
cd <path-to-repo>
./setup.ps1
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

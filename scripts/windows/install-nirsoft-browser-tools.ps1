<#
.SYNOPSIS
  Install NirSoft Web Browser Tools bundle and create desktop shortcuts.

.DESCRIPTION
  Downloads a curated set of NirSoft browser forensics utilities from
  https://www.nirsoft.net/web_browser_tools.html and extracts them into:
     C:\Tools\NirSoftBrowserTools
  Adds that directory to PATH and creates desktop shortcuts (unless skipped).

.NOTES
  - Each NirSoft utility is distributed as a ZIP containing one or more files.
  - Some tools may trigger AV heuristics; ensure exclusions if needed.
  - All downloads use HTTPS and retry logic via Invoke-SafeDownload.
  - Requires Windows + Administrator (for PATH machine scope).

.PARAMETER Destination
  Root install directory (default C:\Tools\NirSoftBrowserTools).

.PARAMETER ShortcutCategory
  Desktop folder category (default "NirSoft Browser").

.PARAMETER SkipShortcuts
  Skip creating shortcuts if specified.
#>

Set-StrictMode -Version Latest

# Import common module if not already loaded (when standalone)
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-NirSoftBrowserTools {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\NirSoftBrowserTools',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing NirSoft Web Browser Tools bundle...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $installDir = $Destination
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'NirSoft Browser' }

    Ensure-Directory -Path $installDir
    Ensure-Directory -Path $desktopShortcutDir

    # Define list of browser tools (zip file suffix pattern: <tool>.zip)
    # Only include Windows GUI utilities (exclude command-line variants if overlapping)
    $tools = @(
        'BrowsingHistoryView',
        'ChromeCacheView',
        'ChromeCookiesView',
        'ChromeHistoryView',
        'ChromePass',
        'IECacheView',
        'IECookiesView',
        'IEHistoryView',
        'MZCookiesView',  # Firefox cookies (legacy name)
        'MZCacheView',    # Firefox cache (legacy)
        'MZHistoryView',  # Firefox history (legacy)
        'MozillaCacheView',
        'MozillaCookiesView',
        'MozillaHistoryView',
        'OperaCacheView',
        'SafariCacheView',
        'WebBrowserPassView',
        'MyLastSearch',
        'FlashCookiesView',
        'VideoCacheView'
    )

    # Some tools changed names over time; include modern equivalents mapping
    $altMap = @{ }

    $baseUrl = 'https://www.nirsoft.net/toolsdownload'

    $downloadFailures = @()

    foreach ($tool in $tools) {
        $zipName = "$tool.zip"
        $url = "$baseUrl/$zipName"
        $outZip = Join-Path $env:TEMP $zipName
        Write-Log -Level Info -Message "Downloading $tool..."
        try {
            Invoke-SafeDownload -Uri $url -OutFile $outZip | Out-Null
        } catch {
            Write-Log -Level Warn -Message "Failed: $tool ($($_.Exception.Message))"
            $downloadFailures += $tool
            continue
        }
        if (-not (Test-Path -LiteralPath $outZip)) {
            Write-Log -Level Warn -Message "Archive missing after download: $tool"
            $downloadFailures += $tool
            continue
        }
        $toolDir = Join-Path $installDir $tool
        Ensure-Directory -Path $toolDir
        try {
            Expand-Zip -ZipPath $outZip -Destination $toolDir
        } catch {
            Write-Log -Level Warn -Message "Extraction failed for $tool: $($_.Exception.Message)"
            $downloadFailures += $tool
            continue
        } finally {
            try { Remove-Item -Path $outZip -Force -ErrorAction SilentlyContinue } catch { }
        }
        Write-Log -Level Success -Message "$tool ready."        
    }

    # Add root directory to PATH
    try { Add-PathIfMissing -Path $installDir -Scope Machine } catch { Write-Log -Level Warn -Message "Failed adding PATH: $($_.Exception.Message)" }

    # Create shortcuts for all EXE files across all subfolders (unless skipped)
    if (-not $SkipShortcuts) {
        try {
            $shell = New-Object -ComObject WScript.Shell
            Get-ChildItem -Path $installDir -Recurse -Filter '*.exe' -File -ErrorAction SilentlyContinue | ForEach-Object {
                $lnk = Join-Path $desktopShortcutDir ("$($_.BaseName).lnk")
                $sc = $shell.CreateShortcut($lnk)
                $sc.TargetPath = $_.FullName
                $sc.WorkingDirectory = $_.Directory.FullName
                $sc.WindowStyle = 1
                $sc.Description = $_.BaseName
                $sc.Save()
            }
            Write-Log -Level Success -Message 'Shortcuts created for NirSoft browser tools.'
        } catch {
            Write-Log -Level Warn -Message "Shortcut creation encountered errors: $($_.Exception.Message)"
        }
    }

    if ($downloadFailures.Count -gt 0) {
        Write-Log -Level Warn -Message ("Failed to fetch: " + ($downloadFailures -join ', '))
    }

    Write-Log -Level Success -Message 'NirSoft Web Browser Tools installation completed.'
}

# Dot-sourced by orchestrator; not auto-executed.

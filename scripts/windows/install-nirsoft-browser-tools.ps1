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

    # Define requested browser tools and download-name fallbacks.
    $toolRequests = @(
        @{ Display = 'BrowsingHistoryView'; Candidates = @('BrowsingHistoryView') },
        @{ Display = 'Session History Scrounger'; Candidates = @('SessionHistoryView', 'SessionHistoryScrounger') },
        @{ Display = 'ESEDatabaseView'; Candidates = @('ESEDatabaseView') },
        @{ Display = 'ChromeCacheView'; Candidates = @('ChromeCacheView') },
        @{ Display = 'ChromeCookiesView'; Candidates = @('ChromeCookiesView') },
        @{ Display = 'ChromeHistoryView'; Candidates = @('ChromeHistoryView') },
        @{ Display = 'ChromePass'; Candidates = @('ChromePass') },
        @{ Display = 'IECacheView'; Candidates = @('IECacheView') },
        @{ Display = 'IECookiesView'; Candidates = @('IECookiesView') },
        @{ Display = 'IEHistoryView'; Candidates = @('IEHistoryView') },
        @{ Display = 'MZCookiesView'; Candidates = @('MZCookiesView') },       # Firefox cookies (legacy name)
        @{ Display = 'MZCacheView'; Candidates = @('MZCacheView') },           # Firefox cache (legacy)
        @{ Display = 'MZHistoryView'; Candidates = @('MZHistoryView') },       # Firefox history (legacy)
        @{ Display = 'MozillaCacheView'; Candidates = @('MozillaCacheView') },
        @{ Display = 'MozillaCookiesView'; Candidates = @('MozillaCookiesView') },
        @{ Display = 'MozillaHistoryView'; Candidates = @('MozillaHistoryView') },
        @{ Display = 'OperaCacheView'; Candidates = @('OperaCacheView') },
        @{ Display = 'SafariCacheView'; Candidates = @('SafariCacheView') },
        @{ Display = 'WebBrowserPassView'; Candidates = @('WebBrowserPassView') },
        @{ Display = 'MyLastSearch'; Candidates = @('MyLastSearch') },
        @{ Display = 'FlashCookiesView'; Candidates = @('FlashCookiesView') },
        @{ Display = 'VideoCacheView'; Candidates = @('VideoCacheView') }
    )

    $baseUrl = 'https://www.nirsoft.net/toolsdownload'

    $downloadFailures = @()

    foreach ($request in $toolRequests) {
        $displayName = [string]$request.Display
        $candidates = @($request.Candidates)
        if (-not $candidates -or $candidates.Count -eq 0) { $candidates = @($displayName) }

        $downloadedZip = $null
        $downloadedAs = $null

        foreach ($candidate in $candidates) {
            $zipName = "$candidate.zip"
            $url = "$baseUrl/$zipName"
            $outZip = Join-Path $env:TEMP $zipName
            Write-Log -Level Info -Message "Downloading $displayName (candidate: $candidate)..."
            try {
                Invoke-SafeDownload -Uri $url -OutFile $outZip | Out-Null
                if (Test-Path -LiteralPath $outZip) {
                    $downloadedZip = $outZip
                    $downloadedAs = $candidate
                    break
                }
            } catch { }
        }

        if (-not $downloadedZip) {
            Write-Log -Level Warn -Message "Failed: $displayName"
            $downloadFailures += $displayName
            continue
        }

        $toolDirName = ($displayName -replace '[\\/:*?"<>|]', '_')
        $toolDir = Join-Path $installDir $toolDirName
        Ensure-Directory -Path $toolDir
        try {
            Expand-Zip -ZipPath $downloadedZip -Destination $toolDir
        } catch {
            Write-Log -Level Warn -Message "Extraction failed for $displayName: $($_.Exception.Message)"
            $downloadFailures += $displayName
            continue
        } finally {
            try { if ($downloadedZip) { Remove-Item -Path $downloadedZip -Force -ErrorAction SilentlyContinue } } catch { }
        }
        Write-Log -Level Success -Message "$displayName ready (download: $downloadedAs)."        
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

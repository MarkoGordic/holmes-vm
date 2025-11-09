function Install-Chainsaw {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\Chainsaw',
        [switch]$InstallRules = $true,
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    # Ensure common helpers are available when run standalone
    try {
        if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
            $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
            if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
        }
    } catch { }

    Write-Log -Level Info -Message 'Installing Chainsaw...'

    $installDir = $Destination
    $zipPath = Join-Path $env:TEMP 'chainsaw.zip'
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'Chainsaw' }
    $rulesRoot = Join-Path $installDir 'rules'

    Ensure-Directory -Path $installDir
    Ensure-Directory -Path $desktopShortcutDir
    Ensure-Directory -Path $rulesRoot

    # Determine platform archive (we target Windows x64)
    # Chainsaw releases use names like chainsaw_x86_64-pc-windows-msvc.zip
    $releaseApi = 'https://api.github.com/repos/WithSecureLabs/chainsaw/releases/latest'
    Set-Tls12IfNeeded
    try {
        $resp = Invoke-RestMethod -Uri $releaseApi -UseBasicParsing -ErrorAction Stop
        $asset = $resp.assets | Where-Object { $_.name -match 'windows.*\.zip$' } | Select-Object -First 1
        if (-not $asset) { throw 'No Windows ZIP asset found for Chainsaw latest release.' }
        $downloadUrl = $asset.browser_download_url
    } catch {
        Write-Log -Level Warn -Message "Failed to query Chainsaw release API: $($_.Exception.Message). Falling back to hardcoded asset name."
        $downloadUrl = 'https://github.com/WithSecureLabs/chainsaw/releases/latest/download/chainsaw_x86_64-pc-windows-msvc.zip'
    }

    Invoke-SafeDownload -Uri $downloadUrl -OutFile $zipPath
    Expand-Zip -ZipPath $zipPath -Destination $installDir

    # Find chainsaw.exe within extracted folder
    $exe = Get-ChildItem -Path $installDir -Recurse -Filter 'chainsaw.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($exe) {
        $binDir = $exe.Directory.FullName
        # Ensure both the exe directory and root install dir are on PATH for convenience
        Add-PathIfMissing -Path $binDir -Scope Machine
        Add-PathIfMissing -Path $installDir -Scope Machine

        # Optionally fetch Sigma rules
        if ($InstallRules) {
            $sigmaZip = Join-Path $env:TEMP 'sigma-rules.zip'
            $sigmaBase = Join-Path $rulesRoot 'sigma'
            Ensure-Directory -Path $sigmaBase
            $sigmaUrlPrimary = 'https://github.com/SigmaHQ/sigma/archive/refs/heads/main.zip'
            $sigmaUrlFallback = 'https://github.com/SigmaHQ/sigma/archive/refs/heads/master.zip'
            try {
                Invoke-SafeDownload -Uri $sigmaUrlPrimary -OutFile $sigmaZip
            } catch {
                Write-Log -Level Warn -Message "Sigma main.zip not reachable. Trying master.zip..."
                Invoke-SafeDownload -Uri $sigmaUrlFallback -OutFile $sigmaZip
            }
            Expand-Zip -ZipPath $sigmaZip -Destination $sigmaBase
            # Flatten sigma-main/master folder if present
            $sigmaExtracted = Get-ChildItem -Path $sigmaBase -Directory | Where-Object { $_.Name -like 'sigma-*' } | Select-Object -First 1
            if ($sigmaExtracted) {
                Get-ChildItem -Path $sigmaExtracted.FullName -Force | Move-Item -Destination $sigmaBase -Force
                Remove-Item -Path $sigmaExtracted.FullName -Recurse -Force
            }
        }

        # Remove any legacy quick-run artifacts if present
        $wrapperPath = Join-Path $installDir 'chainsaw-quickhunt.ps1'
        $shimPath = Join-Path $installDir 'chainsaw-quickhunt.cmd'
        if (Test-Path -LiteralPath $wrapperPath) {
            if ($PSCmdlet.ShouldProcess($wrapperPath, 'Remove legacy quick-hunt wrapper')) {
                Remove-Item -Path $wrapperPath -Force -ErrorAction SilentlyContinue
            }
        }
        if (Test-Path -LiteralPath $shimPath) {
            if ($PSCmdlet.ShouldProcess($shimPath, 'Remove legacy quick-hunt shim')) {
                Remove-Item -Path $shimPath -Force -ErrorAction SilentlyContinue
            }
        }

        # Create desktop shortcuts only if not skipped
        if (-not $SkipShortcuts) {
            New-ShortcutsFromFolder -Folder $binDir -Filter 'chainsaw.exe' -ShortcutDir $desktopShortcutDir -WorkingDir $binDir
        }
        Write-Log -Level Success -Message 'Chainsaw installed.'
    } else {
        Write-Log -Level Warn -Message 'chainsaw.exe not found after extraction.'
    }
}

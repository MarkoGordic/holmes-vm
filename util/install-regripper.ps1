function Install-RegRipper {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\RegRipper4.0'
    )

    Write-Log -Level Info -Message 'Installing RegRipper 4.0...'

    $regripperDir = $Destination
    $zipUrl = 'https://github.com/keydet89/RegRipper4.0/archive/refs/heads/main.zip'
    $zipPath = Join-Path $env:TEMP 'RegRipper4.0.zip'
    $desktopShortcutDir = Join-Path (Join-Path $env:USERPROFILE 'Desktop') 'RegRipper4.0'

    Ensure-Directory -Path $regripperDir
    Ensure-Directory -Path $desktopShortcutDir

    Invoke-SafeDownload -Uri $zipUrl -OutFile $zipPath
    Expand-Zip -ZipPath $zipPath -Destination $regripperDir

    # If the extracted folder is RegRipper4.0-main, move its contents up
    $mainFolder = Join-Path $regripperDir 'RegRipper4.0-main'
    if (Test-Path -LiteralPath $mainFolder) {
        Get-ChildItem -Path $mainFolder -Force | ForEach-Object {
            $dest = Join-Path $regripperDir $_.Name
            try {
                if (Test-Path -LiteralPath $dest) {
                    # Skip existing files to avoid "already exists" errors
                    return
                }
                Move-Item -Path $_.FullName -Destination $regripperDir -Force -ErrorAction Stop
            } catch {
                Write-Log -Level Warn -Message "Could not move $($_.Name): $($_.Exception.Message)"
            }
        }
        try { Remove-Item -Path $mainFolder -Recurse -Force -ErrorAction Stop } catch { }
    }

    # Create shortcuts to all .exe files in RegRipper4.0 on Desktop
    New-ShortcutsFromFolder -Folder $regripperDir -Filter '*.exe' -ShortcutDir $desktopShortcutDir -WorkingDir $regripperDir
    Write-Log -Level Success -Message 'Shortcuts to RegRipper 4.0 created on Desktop.'
}

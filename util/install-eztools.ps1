function Install-EZTools {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\EricZimmermanTools',
        [string]$NetVersion = '6'
    )

    Write-Log -Level Info -Message "Installing Eric Zimmerman's Tools..."

    $ezToolsDir = $Destination
    $ezToolsZip = Join-Path $env:TEMP 'Get-ZimmermanTools.zip'
    $ezToolsScript = Join-Path $ezToolsDir 'Get-ZimmermanTools.ps1'
    $ezToolsNetDir = Join-Path $ezToolsDir ("net$NetVersion")
    $desktopShortcutDir = Join-Path (Join-Path $env:USERPROFILE 'Desktop') 'EricZimmermanTools'

    Ensure-Directory -Path $ezToolsDir
    Ensure-Directory -Path $desktopShortcutDir

    # Download Get-ZimmermanTools.zip
    Invoke-SafeDownload -Uri 'https://f001.backblazeb2.com/file/EricZimmermanTools/Get-ZimmermanTools.zip' -OutFile $ezToolsZip

    # Extract the ZIP file and unblock script
    Expand-Zip -ZipPath $ezToolsZip -Destination $ezToolsDir
    if (Test-Path -LiteralPath $ezToolsScript) { Unblock-File -Path $ezToolsScript }

    # Run the script to download the tools
    Push-Location $ezToolsDir
    try {
        if ($PSCmdlet.ShouldProcess('Get-ZimmermanTools.ps1', 'Execute')) {
            .\Get-ZimmermanTools.ps1 -Dest $ezToolsDir -NetVersion $NetVersion
        }
    }
    finally { Pop-Location }

    # Add EZ Tools to system PATH (both root and netX if present)
    if (Test-Path -LiteralPath $ezToolsDir) {
        Add-PathIfMissing -Path $ezToolsDir -Scope Machine
    }
    if (Test-Path -LiteralPath $ezToolsNetDir) {
        Add-PathIfMissing -Path $ezToolsNetDir -Scope Machine
    } else {
        Write-Log -Level Warn -Message "Expected tools directory not found: $ezToolsNetDir"
    }

    # Create shortcuts to all .exe files in netX folder on Desktop
    if (Test-Path -LiteralPath $ezToolsNetDir) {
        New-ShortcutsFromFolder -Folder $ezToolsNetDir -ShortcutDir $desktopShortcutDir -WorkingDir $ezToolsNetDir
    }

    # Ensure MFTExplorer shortcut exists even if not under netX
    $mft = Get-ChildItem -Path $ezToolsDir -Recurse -Filter 'MFTExplorer.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($mft) {
        $shell = New-Object -ComObject WScript.Shell
        $lnk = Join-Path $desktopShortcutDir 'MFTExplorer.exe.lnk'
        $sc = $shell.CreateShortcut($lnk)
        $sc.TargetPath = $mft.FullName
        $sc.WorkingDirectory = $mft.Directory.FullName
        $sc.WindowStyle = 1
        $sc.Description = 'MFT Explorer'
        $sc.Save()
    }

    Write-Log -Level Success -Message "Shortcuts to Eric Zimmerman's Tools created on Desktop."
}

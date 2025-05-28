function Install-RegRipper {
    Write-Host "Installing RegRipper 4.0..." -ForegroundColor Magenta

    $regripperDir = "C:\\Tools\\RegRipper4.0"
    $zipUrl = "https://github.com/keydet89/RegRipper4.0/archive/refs/heads/main.zip"
    $zipPath = "$env:TEMP\RegRipper4.0.zip"
    $desktopShortcutDir = "$env:USERPROFILE\Desktop\RegRipper4.0"

    # Create directories if they don't exist
    if (-not (Test-Path -Path $regripperDir)) {
        New-Item -ItemType Directory -Path $regripperDir | Out-Null
    }
    if (-not (Test-Path -Path $desktopShortcutDir)) {
        New-Item -ItemType Directory -Path $desktopShortcutDir | Out-Null
    }

    # Download the ZIP archive
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath

    # Extract the ZIP archive
    Expand-Archive -Path $zipPath -DestinationPath $regripperDir -Force

    # If the extracted folder is RegRipper4.0-main, move its contents up
    $mainFolder = Join-Path $regripperDir 'RegRipper4.0-main'
    if (Test-Path $mainFolder) {
        Get-ChildItem -Path $mainFolder | Move-Item -Destination $regripperDir -Force
        Remove-Item -Path $mainFolder -Recurse -Force
    }

    # Create shortcuts to all .exe files in RegRipper4.0 on Desktop
    $shell = New-Object -ComObject WScript.Shell
    Get-ChildItem -Path $regripperDir -Filter *.exe | ForEach-Object {
        $shortcut = $shell.CreateShortcut("$desktopShortcutDir\$($_.Name).lnk")
        $shortcut.TargetPath = $_.FullName
        $shortcut.WorkingDirectory = $regripperDir
        $shortcut.WindowStyle = 1
        $shortcut.Description = $_.BaseName
        $shortcut.Save()
    }
    Write-Host "Shortcuts to RegRipper 4.0 created on Desktop." -ForegroundColor Green
}

function Install-EZTools {
    Write-Host "Installing Eric Zimmerman's Tools..." -ForegroundColor Magenta

    $ezToolsDir = "C:\\Tools\\EricZimmermanTools"
    $ezToolsZip = "$env:TEMP\Get-ZimmermanTools.zip"
    $ezToolsScript = "$ezToolsDir\Get-ZimmermanTools.ps1"
    $ezToolsNetDir = "$ezToolsDir\net6"
    $desktopShortcutDir = "$env:USERPROFILE\Desktop\EricZimmermanTools"

    # Create directories if they don't exist
    if (-not (Test-Path -Path $ezToolsDir)) {
        New-Item -ItemType Directory -Path $ezToolsDir | Out-Null
    }
    if (-not (Test-Path -Path $desktopShortcutDir)) {
        New-Item -ItemType Directory -Path $desktopShortcutDir | Out-Null
    }

    # Download Get-ZimmermanTools.zip
    Invoke-WebRequest -Uri "https://f001.backblazeb2.com/file/EricZimmermanTools/Get-ZimmermanTools.zip" -OutFile $ezToolsZip

    # Extract the ZIP file
    Expand-Archive -Path $ezToolsZip -DestinationPath $ezToolsDir -Force

    # Unblock the PowerShell script
    Unblock-File -Path $ezToolsScript

    # Run the script to download the tools
    Set-Location -Path $ezToolsDir
    .\Get-ZimmermanTools.ps1 -Dest $ezToolsDir -NetVersion 6

    # Add EZ Tools to system PATH
    if (-not ($env:Path -like "*$ezToolsNetDir*")) {
        [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$ezToolsNetDir", [EnvironmentVariableTarget]::Machine)
        Write-Host "EZ Tools path added to system PATH." -ForegroundColor Green
    }
    else {
        Write-Host "EZ Tools path already exists in system PATH." -ForegroundColor Yellow
    }

    # Create shortcuts to all .exe files in net6 folder on Desktop
    $shell = New-Object -ComObject WScript.Shell
    Get-ChildItem -Path $ezToolsNetDir -Filter *.exe | ForEach-Object {
        $shortcut = $shell.CreateShortcut("$desktopShortcutDir\$($_.Name).lnk")
        $shortcut.TargetPath = $_.FullName
        $shortcut.WorkingDirectory = $ezToolsNetDir
        $shortcut.WindowStyle = 1
        $shortcut.Description = $_.BaseName
        $shortcut.Save()
    }
    Write-Host "Shortcuts to Eric Zimmerman's Tools created on Desktop." -ForegroundColor Green
}

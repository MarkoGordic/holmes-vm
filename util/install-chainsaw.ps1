function Install-Chainsaw {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\Chainsaw',
        [switch]$InstallRules = $true
    )

    Write-Log -Level Info -Message 'Installing Chainsaw...'

    $installDir = $Destination
    $zipPath = Join-Path $env:TEMP 'chainsaw.zip'
    $desktopShortcutDir = Join-Path (Join-Path $env:USERPROFILE 'Desktop') 'Chainsaw'
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

        # Create quick-hunt wrapper for easy usage
        $wrapperPath = Join-Path $installDir 'chainsaw-quickhunt.ps1'
        $wrapper = @"
param(
    [Parameter(Mandatory)][string]$EvtxPath,
    [string]$RulesPath,
    [string]$MappingPath,
    [switch]$VerboseOutput
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$exe = Get-ChildItem -Path "$binDir" -Filter 'chainsaw.exe' -ErrorAction Stop | Select-Object -First 1
if (-not $exe) { throw 'chainsaw.exe not found.' }
if (-not (Test-Path -LiteralPath $EvtxPath)) { throw "EVTX path not found: $EvtxPath" }
if (-not $RulesPath) {
    $maybe = Join-Path '$rulesRoot' 'sigma/rules/windows'
    if (Test-Path -LiteralPath $maybe) { $RulesPath = $maybe } else { $RulesPath = Join-Path '$rulesRoot' 'sigma/rules' }
}
if (-not (Test-Path -LiteralPath $RulesPath)) { throw "Rules path not found: $RulesPath" }
if (-not $MappingPath) {
    $mapDir = Join-Path '$installDir' 'mappings'
    if (Test-Path -LiteralPath $mapDir) {
        $candidate = Get-ChildItem -Path $mapDir -Filter '*sigma*windows*.yml' -File | Select-Object -First 1
        if (-not $candidate) { $candidate = Get-ChildItem -Path $mapDir -Filter '*.yml' -File | Select-Object -First 1 }
        if ($candidate) { $MappingPath = $candidate.FullName }
    }
}
if (-not $MappingPath) {
    Write-Host 'Mapping file not found. Chainsaw may still run but results could be limited.' -ForegroundColor Yellow
}
$args = @('hunt','-s', $RulesPath)
if ($MappingPath) { $args += @('-m', $MappingPath) }
if ($VerboseOutput) { $args += '-v' }
$args += $EvtxPath
& $exe.FullName @args
"@
        if ($PSCmdlet.ShouldProcess($wrapperPath, 'Create quick-hunt wrapper')) {
            $wrapper | Set-Content -Path $wrapperPath -Encoding UTF8 -Force
        }

        # Create desktop shortcuts
        New-ShortcutsFromFolder -Folder $binDir -Filter 'chainsaw.exe' -ShortcutDir $desktopShortcutDir -WorkingDir $binDir
        New-ShortcutsFromFolder -Folder $installDir -Filter 'chainsaw-quickhunt.ps1' -ShortcutDir $desktopShortcutDir -WorkingDir $installDir
        Write-Log -Level Success -Message 'Chainsaw installed.'
    } else {
        Write-Log -Level Warn -Message 'chainsaw.exe not found after extraction.'
    }
}

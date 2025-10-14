Set-StrictMode -Version Latest

Describe 'Common module loads' {
    It 'imports Holmes.Common without error' {
        { Import-Module "$PSScriptRoot/../modules/Holmes.Common.psm1" -Force } | Should -Not -Throw
    }
}

Describe 'Helper functions exist' {
    BeforeAll { Import-Module "$PSScriptRoot/../modules/Holmes.Common.psm1" -Force }
    It 'has Write-Log' { Get-Command Write-Log -ErrorAction Stop | Should -Not -BeNullOrEmpty }
    It 'has Ensure-Chocolatey' { Get-Command Ensure-Chocolatey -ErrorAction Stop | Should -Not -BeNullOrEmpty }
}

Context 'Dry-run installers' {
    BeforeAll {
        . "$PSScriptRoot/../util/install-eztools.ps1"
        . "$PSScriptRoot/../util/install-regripper.ps1"
        . "$PSScriptRoot/../util/install-chainsaw.ps1"
        . "$PSScriptRoot/../util/install-zui.ps1"
    }
    It 'Install-EZTools supports WhatIf' {
        { Install-EZTools -WhatIf } | Should -Not -Throw
    }
    It 'Install-RegRipper supports WhatIf' {
        { Install-RegRipper -WhatIf } | Should -Not -Throw
    }
    It 'Install-Chainsaw supports WhatIf' {
        { Install-Chainsaw -WhatIf } | Should -Not -Throw
    }
    It 'Install-Zui supports WhatIf' {
        { Install-Zui -WhatIf } | Should -Not -Throw
    }
}

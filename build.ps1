param([string]$Assembler)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not $Assembler) {
        $command = Get-Command jwasm.exe -ErrorAction SilentlyContinue
        if (-not $command) { $command = Get-Command jwasm -ErrorAction SilentlyContinue }
        if (-not $command) { throw 'Install JWasm or pass -Assembler C:\tools\jwasm.exe.' }
        $Assembler = $command.Source
    }
    foreach ($font in 'fonts/GTHAI1-19.FON', 'fonts/GTHAI2-19.FON') {
        if ((Get-Item -LiteralPath $font).Length -ne 4864) {
            throw "$font must contain 256 glyphs of 19 bytes each (4864 bytes)."
        }
    }
    New-Item -ItemType Directory -Force work,output | Out-Null
    # Stage both builds first; leave release files intact if either build fails.
    foreach ($target in 'GTHAI','GTHAI386') {
        $arguments = @('-bin', "-Fowork/$target.COM", "-Flwork/$target.lst")
        if ($target -eq 'GTHAI386') { $arguments += '-DCPU_386=1' }
        $arguments += 'GTHAI.ASM'
        & $Assembler @arguments
        if ($LASTEXITCODE -ne 0) { throw "Assembler failed for $target ($LASTEXITCODE); outputs were not replaced." }
        $binary = Get-Item -LiteralPath "work/$target.COM"
        if ($binary.Length -lt 256 -or $binary.Length -gt 65280) { throw "Invalid DOS COM size for $target." }
    }
    foreach ($target in 'GTHAI','GTHAI386') {
        Copy-Item -LiteralPath "work/$target.COM" -Destination "output/$target.COM" -Force
        $binary = Get-Item -LiteralPath "output/$target.COM"
        Write-Output "Built output/$target.COM ($($binary.Length) bytes)"
    }
} finally {
    Pop-Location
}

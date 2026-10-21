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
    & $Assembler '-bin' '-Fowork/GTHAI.COM' '-Flwork/GTHAI.lst' 'GTHAI.ASM'
    if ($LASTEXITCODE -ne 0) { throw "Assembler failed ($LASTEXITCODE); output was not replaced." }
    $binary = Get-Item -LiteralPath 'work/GTHAI.COM'
    if ($binary.Length -lt 256 -or $binary.Length -gt 65280) { throw 'Invalid DOS COM file size.' }
    Copy-Item -LiteralPath 'work/GTHAI.COM' -Destination 'output/GTHAI.COM' -Force
    Write-Output "Built output\GTHAI.COM ($($binary.Length) bytes)"
} finally {
    Pop-Location
}

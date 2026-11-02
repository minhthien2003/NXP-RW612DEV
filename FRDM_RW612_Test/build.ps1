param(
    [string]$KeilRoot = 'C:\Keil_v5',
    [switch]$Rebuild
)
$ErrorActionPreference = 'Stop'
$uv4 = Join-Path $KeilRoot 'UV4\UV4.exe'
if (!(Test-Path -LiteralPath $uv4)) { throw "Khong tim thay Keil: $uv4" }
$project = Join-Path $PSScriptRoot 'mdk\FRDM_RW612_Test.uvprojx'
$log = Join-Path $PSScriptRoot 'mdk\build.log'
if (Test-Path -LiteralPath $log) { Remove-Item -LiteralPath $log }
$operation = if ($Rebuild) { '-r' } else { '-b' }
$process = Start-Process -FilePath $uv4 -ArgumentList @($operation, ('"' + $project + '"'), '-t', 'flash_debug', '-o', ('"' + $log + '"')) -WindowStyle Hidden -Wait -PassThru
if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log }
# uVision: 0 = success, 1 = warnings only, >=2 = errors.
if ($process.ExitCode -lt 0 -or $process.ExitCode -ge 2) { throw "Keil build failed (exit $($process.ExitCode)). See $log" }

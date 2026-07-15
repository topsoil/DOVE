param(
    [string]$JobName = "dimi-full",
    [int]$Tail = 25
)

$project = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $project "data\results\background"
$pidFile = Join-Path $runDir "$JobName.pid"
$outLog = Join-Path $runDir "$JobName.out.log"
$errLog = Join-Path $runDir "$JobName.err.log"
if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "No PID file for '$JobName'."
} else {
    $jobPid = [int](Get-Content -LiteralPath $pidFile -Raw)
    $process = Get-Process -Id $jobPid -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "RUNNING PID=$jobPid CPU=$([math]::Round($process.CPU, 1))s started=$($process.StartTime)"
    } else {
        Write-Host "NOT RUNNING (last PID=$jobPid). Check logs and output."
    }
}
if (Test-Path -LiteralPath $outLog) {
    Write-Host "`n--- stdout (last $Tail lines) ---"
    Get-Content -LiteralPath $outLog -Tail $Tail
}
if ((Test-Path -LiteralPath $errLog) -and (Get-Item -LiteralPath $errLog).Length -gt 0) {
    Write-Host "`n--- stderr (last $Tail lines) ---"
    Get-Content -LiteralPath $errLog -Tail $Tail
}

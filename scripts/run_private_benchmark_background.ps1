param(
    [ValidateSet("direct", "wiki")]
    [string]$Strategy = "wiki",
    [Parameter(Mandatory = $true)]
    [string]$Documents,
    [Parameter(Mandatory = $true)]
    [string]$Domain,
    [int]$Questions = 120,
    [string]$Output = "data\generated_questions\dimi_full_120.json",
    [string]$Workspace = "data\corpora\dimi_full_wiki",
    [string]$OllamaModel = "qwen3:4b",
    [string]$ModelsConfig = "",
    [string]$ModelName = "",
    [int]$Parallel = 1,
    [int]$OllamaContext = 8192,
    [int]$MaxOutputTokens = 900,
    [int]$WikiChunkChars = 24000,
    [int]$QuestionContextChars = 40000,
    [int]$SourceChunkChars = 40000,
    [int]$BatchSize = 10,
    [int]$MaxRounds = 10,
    [string]$JobName = "dimi-full"
)

$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
$documentsPath = (Resolve-Path -LiteralPath $Documents).Path
$python = (Get-Command python -ErrorAction Stop).Source
$runDir = Join-Path $project "data\results\background"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$pidFile = Join-Path $runDir "$JobName.pid"
$outLog = Join-Path $runDir "$JobName.out.log"
$errLog = Join-Path $runDir "$JobName.err.log"

if (Test-Path -LiteralPath $pidFile) {
    $oldPid = [int](Get-Content -LiteralPath $pidFile -Raw)
    if (Get-Process -Id $oldPid -ErrorAction SilentlyContinue) {
        throw "Job '$JobName' is already running as PID $oldPid."
    }
}
if ($ModelsConfig -and $OllamaModel -ne "qwen3:4b") {
    throw "Specify either -ModelsConfig or -OllamaModel, not both."
}

$argsList = @(
    "-u", "scripts\generate_private_benchmark.py",
    "--strategy", $Strategy,
    "--documents", $documentsPath,
    "--domain", $Domain,
    "--n", "$Questions",
    "--output", $Output,
    "--workspace", $Workspace,
    "--parallel", "$Parallel",
    "--batch-size", "$BatchSize",
    "--max-rounds", "$MaxRounds",
    "--max-output-tokens", "$MaxOutputTokens"
)
if ($ModelsConfig) {
    $argsList += @("--models", $ModelsConfig)
    if ($ModelName) { $argsList += @("--model", $ModelName) }
    $argsList += "--structured-outputs"
} else {
    $argsList += @("--ollama-model", $OllamaModel, "--ollama-context", "$OllamaContext")
}
if ($Strategy -eq "wiki") {
    $argsList += @("--wiki-chunk-chars", "$WikiChunkChars",
                   "--question-context-chars", "$QuestionContextChars")
} else {
    $argsList += @("--source-chunk-chars", "$SourceChunkChars")
}

function Quote-Argument([string]$value) {
    if ($value -match '[\s"]') { return '"' + $value.Replace('"', '\"') + '"' }
    return $value
}
$argumentString = ($argsList | ForEach-Object { Quote-Argument $_ }) -join " "
$process = Start-Process -FilePath $python -ArgumentList $argumentString `
    -WorkingDirectory $project -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog -WindowStyle Hidden -PassThru
Set-Content -LiteralPath $pidFile -Value $process.Id -Encoding ascii

Write-Host "Started $Strategy job '$JobName' as PID $($process.Id)."
Write-Host "Output: $Output"
Write-Host "Workspace: $Workspace"
Write-Host "Stdout: $outLog"
Write-Host "Stderr: $errLog"
Write-Host "Status: .\scripts\status_private_benchmark.ps1 -JobName '$JobName'"

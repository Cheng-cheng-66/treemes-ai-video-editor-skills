param(
    [switch]$InstallSystemDependencies
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.11+ is required."
}

$Missing = @()
foreach ($Command in @("ffmpeg", "ffprobe", "node")) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        $Missing += $Command
    }
}

if ($Missing.Count -gt 0 -and -not $InstallSystemDependencies) {
    throw "Missing: $($Missing -join ', '). Install FFmpeg and Node.js, or rerun with -InstallSystemDependencies."
}

if ($InstallSystemDependencies) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is required for automatic system dependency installation."
    }
    if ($Missing -contains "ffmpeg" -or $Missing -contains "ffprobe") {
        winget install --id Gyan.FFmpeg --exact --accept-package-agreements --accept-source-agreements
    }
    if ($Missing -contains "node") {
        winget install --id OpenJS.NodeJS.LTS --exact --accept-package-agreements --accept-source-agreements
    }
}

python "$ProjectDir/scripts/bootstrap.py"
exit $LASTEXITCODE

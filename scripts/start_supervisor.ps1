param([switch]$InstallStartup)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskRuntime = Join-Path $taskRoot '.runtime'
New-Item -ItemType Directory -Force -Path $taskRuntime | Out-Null
$taskScript = Join-Path $PSScriptRoot 'supervise.py'
$taskUv = (Get-Command uv.exe).Source
$taskDocker = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
$taskDockerProcess = Get-Process 'Docker Desktop' -ErrorAction SilentlyContinue
if (-not $taskDockerProcess -and (Test-Path -LiteralPath $taskDocker)) {
    Start-Process -FilePath $taskDocker -WindowStyle Hidden
}
$taskArguments = 'run --project "' + $taskRoot + '" python "' + $taskScript + '" --research --releases'
$taskProcess = Start-Process -FilePath $taskUv -ArgumentList $taskArguments -WorkingDirectory $taskRoot `
    -RedirectStandardOutput (Join-Path $taskRuntime 'supervisor.log') `
    -RedirectStandardError (Join-Path $taskRuntime 'supervisor.err') -WindowStyle Hidden -PassThru
$taskProcess.Id | Set-Content -LiteralPath (Join-Path $taskRuntime 'supervisor.pid')
if ($InstallStartup) {
    $taskStartup = 'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"'
    New-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' `
        -Name 'CodexHarnessSupervisor' -Value $taskStartup -PropertyType String -Force | Out-Null
}
Write-Output ('Supervisor process started: ' + $taskProcess.Id)

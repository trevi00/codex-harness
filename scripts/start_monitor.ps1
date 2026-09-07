param([switch]$InstallStartup)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskRuntime = Join-Path $taskRoot '.runtime'
New-Item -ItemType Directory -Force -Path $taskRuntime | Out-Null
$taskUv = (Get-Command uv.exe).Source
foreach ($taskMode in @('collect', 'web')) {
    $taskPidFile = Join-Path $taskRuntime ('monitor-' + $taskMode + '.pid')
    $taskExisting = $null
    if (Test-Path -LiteralPath $taskPidFile) {
        $taskExistingId = [int](Get-Content -LiteralPath $taskPidFile)
        $taskExisting = Get-CimInstance Win32_Process -Filter "ProcessId=$taskExistingId" |
            Where-Object { $_.CommandLine -like '*monitor.py*' -and $_.CommandLine -like ('*' + $taskMode + '*') }
    }
    if (-not $taskExisting) {
        $taskArguments = 'run --project "' + $taskRoot + '" python "' + (Join-Path $PSScriptRoot 'monitor.py') + '" ' + $taskMode
        $taskProcess = Start-Process -FilePath $taskUv -ArgumentList $taskArguments -WorkingDirectory $taskRoot `
            -RedirectStandardOutput (Join-Path $taskRuntime ('monitor-' + $taskMode + '.log')) `
            -RedirectStandardError (Join-Path $taskRuntime ('monitor-' + $taskMode + '.err')) -WindowStyle Hidden -PassThru
        $taskProcess.Id | Set-Content -LiteralPath $taskPidFile
    }
}
if ($InstallStartup) {
    $taskStartup = 'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"'
    New-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name CodexHarnessMonitor `
        -Value $taskStartup -PropertyType String -Force | Out-Null
}
Write-Output 'Monitor: http://127.0.0.1:8787'

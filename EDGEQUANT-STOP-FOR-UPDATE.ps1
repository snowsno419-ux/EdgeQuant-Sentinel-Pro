# SAFE EdgeQuant client shutdown helper.
# This DOES NOT touch MT5 terminal or delete the install/config folder.
$ErrorActionPreference = 'Stop'
Write-Host ''
Write-Host 'EdgeQuant update helper - check running clients' -ForegroundColor Cyan
Write-Host 'IMPORTANT: Stop automated trading in EdgeQuant and review all open positions BEFORE closing it.' -ForegroundColor Yellow
Write-Host 'If the engine is managing stops or signals, shutting it down interrupts that automation.' -ForegroundColor Yellow
try {
    $running = @(Get-CimInstance Win32_Process -Filter "Name = 'EdgeQuantSentinel.exe'" -ErrorAction Stop)
} catch {
    Write-Host "Cannot check running processes: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
if ($running.Count -eq 0) {
    Write-Host 'No running EdgeQuantSentinel.exe found. Go back to Setup and press Try again.' -ForegroundColor Green
    Write-Host 'If it still fails, reboot Windows, then run Setup before opening EdgeQuant.'
    exit 0
}
Write-Host ''
Write-Host 'Running EdgeQuant clients:'
foreach ($p in $running) {
    Write-Host ("PID {0} | {1}" -f $p.ProcessId, $p.ExecutablePath)
}
Write-Host ''
Write-Host 'Prefer closing the app using its STOP and Exit buttons first.'
$answer = Read-Host 'Only if EdgeQuant will not exit: type CLOSE to stop ALL EdgeQuantSentinel.exe processes, otherwise press Enter'
if ($answer -cne 'CLOSE') {
    Write-Host 'No process was terminated. Close EdgeQuant normally and retry Setup.'
    exit 0
}
foreach ($p in $running) {
    try {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
        Write-Host "Stopped EdgeQuant PID $($p.ProcessId)" -ForegroundColor Green
    } catch {
        Write-Host "Could not stop PID $($p.ProcessId): $($_.Exception.Message)" -ForegroundColor Red
    }
}
Start-Sleep -Seconds 2
$still = @(Get-CimInstance Win32_Process -Filter "Name = 'EdgeQuantSentinel.exe'" -ErrorAction SilentlyContinue)
if ($still.Count -gt 0) {
    Write-Host 'EdgeQuant is still running; close it using Task Manager and retry.' -ForegroundColor Yellow
    exit 1
}
Write-Host 'EdgeQuant processes closed. Click Try again in Setup.' -ForegroundColor Green

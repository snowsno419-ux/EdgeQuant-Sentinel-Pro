$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot 'dist\EdgeQuantSentinel'
if (-not (Test-Path (Join-Path $root 'EdgeQuantSentinel.exe'))) {
    throw 'dist\EdgeQuantSentinel\EdgeQuantSentinel.exe is missing; run the Windows build first.'
}
$privateSourceNames = @(
    'edgequant_auto.py',
    'edgequant_desktop.py',
    'provider_studio.py',
    'edgequant_cloud.py',
    'edgequant_sinhala_voice_worker.py',
    'INSTALL-SINHALA-FEMALE-VOICE.bat',
    'SINHALA-OFFLINE-VOICE.md'
)
# This script touches only the disposable dist payload, never the developer source tree.
Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        ($privateSourceNames -contains $_.Name) -or
        ($_.Extension -in @('.py', '.pyw')) -or
        ($_.Name -like 'edgequant_*.json') -or
        ($_.Name -like 'edgequant_*.jsonl') -or
        ($_.Name -like '*.session*') -or
        ($_.Name -like '*.log') -or
        ($_.Name -in @('config.json', 'credentials.json', 'token.json', '.env'))
    } |
    Remove-Item -Force
$remaining = Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { ($_.Extension -in @('.py', '.pyw')) -or ($privateSourceNames -contains $_.Name) }
if ($remaining) {
    $names = ($remaining | ForEach-Object { $_.FullName }) -join "`n"
    throw "Client payload still contains project source/build files:`n$names"
}
Write-Host 'Source and runtime-data scrub passed: project .py/.pyw files, sessions, settings, logs and local account data are absent from dist.' -ForegroundColor Green

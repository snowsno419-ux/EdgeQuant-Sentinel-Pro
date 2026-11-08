param(
    [Parameter(Mandatory=$true)][string]$CompilerPath,
    [Parameter(Mandatory=$true)][string]$ScriptPath,
    [Parameter(Mandatory=$true)][string]$LogPath
)
$ErrorActionPreference = 'Continue'
$exitCode = 2
$w = $null
try {
    $w = [System.IO.StreamWriter]::new($LogPath, $false, [System.Text.UTF8Encoding]::new($false))
    $w.AutoFlush = $true
    function Log([string]$msg) {
        Write-Host $msg
        $w.WriteLine($msg)
    }
    Log ('Inno Setup client compiler diagnostic, ' + (Get-Date -Format o))
    Log ('Script: ' + $ScriptPath)
    Log ('ISCC: ' + $CompilerPath)
    if (-not (Test-Path -LiteralPath $CompilerPath -PathType Leaf)) { throw 'ISCC.exe is missing. Install Inno Setup 6.' }
    if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) { throw 'EdgeQuantSentinel-Client.iss not found.' }
    $projectRoot = Split-Path -Parent $ScriptPath
    $payload = Join-Path $projectRoot 'dist\EdgeQuantSentinel'
    $appExe = Join-Path $payload 'EdgeQuantSentinel.exe'
    if (-not (Test-Path -LiteralPath $appExe -PathType Leaf)) { throw ('Frozen EXE missing: ' + $appExe) }
    $icon = Join-Path $projectRoot 'edgequant-icon.ico'
    if (-not (Test-Path -LiteralPath $icon -PathType Leaf)) { throw ('Installer icon missing: ' + $icon) }
    # Make sure this is a scrubbed *client* payload. Never compile if raw source,
    # private sessions or secrets remain in the dist payload.
    $leaks = @(Get-ChildItem -LiteralPath $payload -File -Recurse -ErrorAction Stop |
        Where-Object { ($_.Extension -in @('.py','.pyw')) -or
            ($_.Name -like '*.session*') -or
            ($_.Name -in @('.env','config.json','credentials.json','token.json')) -or
            ($_.Name -like 'edgequant_*.json') -or ($_.Name -like 'edgequant_*.jsonl') })
    if ($leaks.Count -gt 0) { throw ('Client files not scrubbed; refusing to compile. Example: ' + $leaks[0].Name) }
    $outDir = Join-Path $projectRoot 'dist'
    $outFile = Join-Path $outDir 'EdgeQuant-Sentinel-Client-Setup.exe'
    if (Test-Path -LiteralPath $outFile) {
        try { Remove-Item -LiteralPath $outFile -Force -ErrorAction Stop }
        catch { throw ('Old Setup.exe is locked. Close it and try again: ' + $_.Exception.Message) }
    }
    Log ('Payload files: ' + @(Get-ChildItem -LiteralPath $payload -File -Recurse).Count)
    Log 'Calling Inno Setup compiler with NORMAL verbose output (not quiet mode)...'
    # Running from the .iss directory keeps relative Source/SetupIconFile/OutputDir paths stable.
    Push-Location -LiteralPath $projectRoot
    try {
        & $CompilerPath $ScriptPath 2>&1 | ForEach-Object { Log ([string]$_) }
        $exitCode = $LASTEXITCODE
    } finally { Pop-Location }
    if ($null -eq $exitCode) { $exitCode = 90 }
    Log ('ISCC exit code: ' + $exitCode)
    if ($exitCode -ne 0) { throw ('Inno Setup returned exit code ' + $exitCode + '; see Error line above.') }
    if (-not (Test-Path -LiteralPath $outFile -PathType Leaf)) { throw ('Compiler returned success but Setup.exe not found: ' + $outFile) }
    $size = (Get-Item -LiteralPath $outFile).Length
    if ($size -lt 65536) { throw ('Unexpectedly small Setup.exe (' + $size + ' bytes); do not distribute.') }
    Log ('PASS: Inno Setup.exe generated (' + $size + ' bytes)')
    $exitCode = 0
} catch {
    $message = 'ERROR: ' + $_.Exception.Message
    Write-Host $message -ForegroundColor Red
    if ($null -ne $w) { $w.WriteLine($message) }
    $exitCode = 2
} finally {
    if ($null -ne $w) { $w.Dispose() }
}
Write-Host ('Inno diagnostic log: ' + $LogPath)
exit $exitCode

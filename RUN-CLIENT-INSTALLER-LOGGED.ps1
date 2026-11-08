param(
    [Parameter(Mandatory = $true)][string] $BuildScript,
    [Parameter(Mandatory = $true)][string] $LogFile
)
$ErrorActionPreference = 'Continue'
$exitCode = 90
$writer = $null
try {
    $scriptPath = (Resolve-Path -LiteralPath $BuildScript -ErrorAction Stop).Path
    $logFolder = Split-Path -Parent $LogFile
    if (-not (Test-Path -LiteralPath $logFolder)) {
        New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
    }
    # Use an explicit encoding for ALL output. Tee-Object's default appended
    # UTF-16 to a UTF-8 file in Windows PowerShell 5.1, corrupting the log.
    $writer = [System.IO.StreamWriter]::new($LogFile, $false, [System.Text.UTF8Encoding]::new($false))
    $writer.AutoFlush = $true
    $writer.WriteLine(('EdgeQuant Client Installer build started ' + (Get-Date -Format o)))
    $writer.WriteLine(('Build script: ' + $scriptPath))
    Write-Host '[EdgeQuant] Streaming build output and writing a UTF-8 diagnostic log...' -ForegroundColor Cyan
    # Preserve child cmd.exe exit code; never report success on a failing build.
    $cmdLine = 'call "' + $scriptPath + '"'
    & $env:ComSpec /D /C $cmdLine 2>&1 | ForEach-Object {
        $line = [string] $_
        Write-Host $line
        $writer.WriteLine($line)
    }
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 91 }
} catch {
    $message = ('BUILD LAUNCH ERROR: ' + $_.Exception.Message)
    Write-Host $message -ForegroundColor Red
    if ($null -ne $writer) { try { $writer.WriteLine($message) } catch {} }
    $exitCode = 92
} finally {
    if ($null -ne $writer) { $writer.Dispose() }
}
if ($exitCode -eq 0) {
    Write-Host '[EdgeQuant] Client installer builder finished successfully.' -ForegroundColor Green
} else {
    Write-Host ("[EdgeQuant] Build stopped with error code $exitCode. Check the log before distributing anything.") -ForegroundColor Red
}
Write-Host "LOG: $LogFile"
exit $exitCode

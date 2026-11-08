$ErrorActionPreference = 'Continue'
$root = $PSScriptRoot
$report = Join-Path $root 'EDGEQUANT-INSTALLER-DIAGNOSIS.txt'
function Add-Report([string]$line) {
  $line | Out-File -LiteralPath $report -Append -Encoding UTF8
  Write-Host $line
}
function Probe([string]$name, [scriptblock]$operation) {
  Add-Report ''
  Add-Report ('=== ' + $name + ' ===')
  try {
    $output = & $operation 2>&1 | Out-String
    if ($output.Trim()) { Add-Report $output.TrimEnd() } else { Add-Report '(no output)' }
  } catch { Add-Report ('ERROR: ' + $_.Exception.Message) }
}
'Started EdgeQuant Installer Diagnostics' | Out-File -LiteralPath $report -Encoding UTF8
Add-Report ('Time: ' + (Get-Date -Format o))
Add-Report ('Build folder: ' + $root)
Add-Report ('Path length: ' + $root.Length)
if ($root.Length -gt 100) {
  Add-Report 'WARN: long build path. Extract to C:\EQBuild\EdgeQuant and run from there.'
}
Probe 'Windows / architecture' { Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,OSArchitecture | Format-List }
Probe 'Python versions registered by py launcher' { & py -0p }
foreach ($v in @('3.11','3.12','3.13','3.14')) {
  $version = $v
  Probe ('Python ' + $version + ' x64 availability') {
    & py ('-' + $version) -c 'import sys,struct;print(sys.version);print(sys.executable);print(struct.calcsize(chr(80))==8)'
  }
}
Probe 'Fallback Python on PATH' { & python -c 'import sys,struct;print(sys.version);print(sys.executable);print(struct.calcsize(chr(80))==8)' }
$innoA = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
$innoB = Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'
if (Test-Path -LiteralPath $innoA) { Add-Report ('Inno Setup compiler: ' + $innoA) }
elseif (Test-Path -LiteralPath $innoB) { Add-Report ('Inno Setup compiler: ' + $innoB) }
else {
  $fromPath = Get-Command ISCC.exe -ErrorAction SilentlyContinue
  if ($fromPath) { Add-Report ('Inno Setup compiler: ' + $fromPath.Source) }
  else { Add-Report 'WARN: Inno Setup 6 ISCC.exe not found in standard locations or PATH.' }
}
foreach ($f in @('BUILD-CLIENT-INSTALLER.bat','BUILD-CLIENT-INSTALLER-CORE.bat','BUILD-EXE.bat','requirements-build.txt','edgequant_auto.py','edgequant_desktop.py')) {
  $p=Join-Path $root $f
  Add-Report (('Source file: ' + $f + ': ') + (Test-Path -LiteralPath $p))
}
$venvPython=Join-Path $root '.edgequant-build-venv\Scripts\python.exe'
if (Test-Path -LiteralPath $venvPython) {
  Probe 'Private build Python version' { & $venvPython -c 'import sys;print(sys.version);print(sys.executable)' }
  Probe 'Private build dependencies' { & $venvPython -c 'import cryptography,requests,telethon,openpyxl,PyInstaller;print(1)' }
  Probe 'Private build MetaTrader5 module (only installed at EXE build stage)' { & $venvPython -c 'import MetaTrader5;print(1)' }
} else { Add-Report 'Private build environment: not created yet (this alone is not an error).' }
$buildLog=Join-Path $root 'CLIENT-INSTALLER-BUILD.log'
if (Test-Path -LiteralPath $buildLog) {
  Add-Report ''
  Add-Report '=== LAST 90 LINES OF CLIENT-INSTALLER-BUILD.log ==='
  try { Get-Content -LiteralPath $buildLog -Encoding UTF8 -Tail 90 -ErrorAction Stop | ForEach-Object { Add-Report $_ } }
  catch { Add-Report ('LOG READ FAILED: ' + $_.Exception.Message) }
} else { Add-Report 'Build log not found here. Run RUN-CLIENT-INSTALLER-KEEP-OPEN.bat then run this diagnostic again.' }
Add-Report ''
Add-Report '=== WHAT NEXT ==='
Add-Report 'If the build fails, share the LAST ERROR lines from the report or CLIENT-INSTALLER-BUILD.log.'
Add-Report 'Redact phone numbers, Telegram codes, tokens, passwords, account IDs and API secrets before sharing.'

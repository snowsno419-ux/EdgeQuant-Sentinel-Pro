; Inno Setup client installer for EdgeQuant Sentinel.
; Compile only after BUILD-CLIENT-INSTALLER.bat has built and source-scrubbed dist\EdgeQuantSentinel.
#define AppName "EdgeQuant Sentinel"
#define AppVersion "1.9.12"
#define AppBuild "UI-V5.1.13 Client"

[Setup]
AppId={{DB6A8A0F-F2F5-4A31-9A0C-7F09C3431B82}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion} {#AppBuild}
AppPublisher=EdgeQuant Sentinel
DefaultDirName={localappdata}\Programs\EdgeQuant Sentinel
DefaultGroupName=EdgeQuant Sentinel
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=dist
OutputBaseFilename=EdgeQuant-Sentinel-Client-Setup
SetupIconFile=edgequant-icon.ico
UninstallDisplayIcon={app}\EdgeQuantSentinel.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
; Detect running EdgeQuant client before any attempt to replace bundled DLLs.
; DLLs can be locked while the app is running, causing DeleteFile code 5.
CloseApplicationsFilter=*.exe,*.dll,*.pyd
AppMutex=EdgeQuantSentinelClient_UpdateGuard_DB6A8A0FF2F54A319A0C7F09C3431B82
RestartApplications=no
Uninstallable=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; The desktop shortcut is always created after installation, including upgrades.
; The branding is stored in the installed payload and not dependent on Windows
; extracting an icon from the EXE or retaining a previously cached shortcut icon.

[Files]
; Source .py files are excluded again here as a fail-safe. Runtime modules and Python
; are bundled by PyInstaller in the onedir folder; clients do not need system Python.
Source: "dist\EdgeQuantSentinel\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.py,*.pyw"

[Icons]
Name: "{autoprograms}\EdgeQuant Sentinel"; Filename: "{app}\EdgeQuantSentinel.exe"; WorkingDir: "{app}"; IconFilename: "{app}\edgequant-icon.ico"
Name: "{autodesktop}\EdgeQuant Sentinel"; Filename: "{app}\EdgeQuantSentinel.exe"; WorkingDir: "{app}"; IconFilename: "{app}\edgequant-icon.ico"

[Run]
Filename: "{app}\EdgeQuantSentinel.exe"; Description: "Launch EdgeQuant Sentinel"; Flags: postinstall nowait skipifsilent

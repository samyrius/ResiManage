#define MyAppName "ResiManage"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "ResiManage"
#define MyAppExeName "ResiManage.exe"

[Setup]
AppId={{B4E6A3B1-9C6E-4E3C-A1D8-2F4C9A7B6D10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\ResiManage
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=release-installer
OutputBaseFilename=ResiManage-2-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Files]
Source: "dist\ResiManage.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\ResiManage"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\ResiManage"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer ResiManage"; Flags: postinstall nowait skipifsilent

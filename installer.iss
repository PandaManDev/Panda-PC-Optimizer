; Inno Setup installer for Panda PC Optimizer
#define AppName "Panda PC Optimizer"
#define AppVersion "0.1.1"
#define AppPublisher "PandaManDev"
#define AppExeName "Panda PC Optimizer.exe"

[Setup]
AppId={{D7D95AC0-6F24-4C6D-9C4D-6C4F5C1D4D81}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Panda PC Optimizer
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Panda PC Optimizer Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}
Uninstallable=yes
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\\Panda PC Optimizer.exe
CreateUninstallRegKey=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\Panda PC Optimizer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Panda PC Optimizer"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\Panda PC Optimizer"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Panda PC Optimizer"; Flags: postinstall nowait skipifsilent

; Digital Crown — Windows per-user installer.
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define MyAppName "DigitalCrown"
#define MyAppPublisher "SANINOVA"
#define MyAppExeName "DigitalCrown.exe"
#define MyAppTaskName "DigitalCrown"
#define MyDistDir "..\dist\DigitalCrown"

[Setup]
AppId={{8F1B6C1E-6C7E-4B7B-9C7C-7E6C1E6C7E6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist_installer
OutputBaseFilename=DigitalCrownSetup-{#MyAppVersion}
Compression=zip
SolidCompression=no
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{sys}\schtasks.exe"; Parameters: "/create /tn ""{#MyAppTaskName}"" /tr ""\""{app}\{#MyAppExeName}\"""" /sc onlogon /rl limited /f"; Flags: runhidden; StatusMsg: "Configuration du démarrage automatique..."
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallRun]
Filename: "{sys}\schtasks.exe"; Parameters: "/delete /tn ""{#MyAppTaskName}"" /f"; Flags: runhidden; RunOnceId: "RemoveDigitalCrownTask"

[UninstallDelete]
; Intentionnellement vide. Les données cabinet vivent sous %APPDATA%\DigitalCrown
; et ne doivent jamais être supprimées par la désinstallation du programme.

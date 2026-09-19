; Digital Crown INSTALLABLE_CERTIFIED cabinet installer.
;
; ABSOLUTE RULE: this installer may only be compiled from a PyInstaller dist that
; already embeds a complete INSTALLABLE_CERTIFIED release proof. DigitalCrown.spec
; enforces the same rule before build, and run.py re-verifies it before first boot.

#define MyAppName "DigitalCrown"
#define MyAppPublisher "SANINOVA"
#define MyAppExeName "DigitalCrown.exe"
#define MyAppTaskName "DigitalCrown"
#define MyDistDir "..\dist\DigitalCrown"

#if !FileExists(MyDistDir + "\release-certification.json")
  #error "INSTALLABLE_CERTIFIED REQUIRED: release-certification.json is missing"
#endif
#if !FileExists(MyDistDir + "\.digitalcrown-release-sha")
  #error "INSTALLABLE_CERTIFIED REQUIRED: .digitalcrown-release-sha is missing"
#endif
#if !FileExists(MyDistDir + "\release-content.sha256")
  #error "INSTALLABLE_CERTIFIED REQUIRED: release-content.sha256 is missing"
#endif
#if !FileExists(MyDistDir + "\installable-certification.json")
  #error "INSTALLABLE_CERTIFIED REQUIRED: installable-certification.json is missing"
#endif
#if !FileExists(MyDistDir + "\runtime-assets-certification.json")
  #error "INSTALLABLE_CERTIFIED REQUIRED: runtime-assets-certification.json is missing"
#endif
#if !FileExists(MyDistDir + "\runtime-assets-content.sha256")
  #error "INSTALLABLE_CERTIFIED REQUIRED: runtime-assets-content.sha256 is missing"
#endif
#if !FileExists(MyDistDir + "\github-attestation-verification.json")
  #error "INSTALLABLE_CERTIFIED REQUIRED: GitHub attestation verification evidence is missing"
#endif

[Setup]
AppId={{8F1B6C1E-6C7E-4B7B-9C7C-7E6C1E6C7E6C}
AppName={#MyAppName}
AppVersion=1.0.0
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist_installer
OutputBaseFilename=DigitalCrownSetup-INSTALLABLE-CERTIFIED
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
; V1 managed update safety:
; copying the certified program files MUST NOT auto-start the application or create
; a startup task. Activation happens only after PREUPDATE backup/rehearsal and an
; explicit cabinet environment has been selected by the controlled update path.

[UninstallRun]
Filename: "{sys}\schtasks.exe"; Parameters: "/delete /tn ""{#MyAppTaskName}"" /f"; \
    Flags: runhidden; RunOnceId: "RemoveDigitalCrownTask"

[UninstallDelete]
; Ne supprime QUE les fichiers programme copiés par [Files].
; %APPDATA%\DigitalCrown\ (données patients, .env, logs, backups) n'est JAMAIS
; supprimé par l'installeur/désinstalleur.

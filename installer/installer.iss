; Anlik Oyun Ceviri - Inno Setup kurulum betigi
; CodeFein sirketi tarafindan gelistirilmistir. Tum haklari saklidir.
; Derlemek:  ISCC.exe installer\installer.iss

#define MyAppName "Anlik Oyun Ceviri"
#define MyAppVersion "1.1.0"
#define MyAppVerName "Anlik Oyun Ceviri 1.1.0 BETA"
#define MyAppPublisher "CodeFein"
#define MyAppExeName "AnlikOyunCeviri.exe"
#define MyAppCopyright "Copyright (c) 2026 CodeFein. Tum haklari saklidir."

[Setup]
AppId={{A0C7E4F1-9D2E-4B6A-8F3C-5A1E2B3C4D5E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppVerName}
AppPublisher={#MyAppPublisher}
AppCopyright={#MyAppCopyright}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} - Gercek zamanli AI oyun ceviri programi
VersionInfoOriginalFileName=AnlikOyunCeviri-Kurulum.exe
DefaultDirName={localappdata}\Programs\AnlikOyunCeviri
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=AnlikOyunCeviri-Kurulum-v{#MyAppVersion}-beta
SetupIconFile=..\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaustu kisa yolu olustur"; GroupDescription: "Kisayollar:"

[Files]
Source: "..\dist\AnlikOyunCeviri\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Kaldir"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName} baslat"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\cache"
Type: filesandordirs; Name: "{app}\_internal\cache"
; Kullanici verisi (ayarlar + ceviri onbellegi) %LOCALAPPDATA%\AnlikOyunCeviri
; altinda tutulur. Onbellek kaldirilir; ayarlar ve API anahtarlari guvenlik
; geregi korunur (kullanici isterse el ile silebilir).
Type: filesandordirs; Name: "{userappdata}\AnlikOyunCeviri\cache"

; Anlık Oyun Çeviri - Inno Setup kurulum betiği
; CodeFein Studio tarafından geliştirilmiştir. Tüm hakları saklıdır.
; Derlemek:  ISCC.exe installer\installer.iss

#define MyAppName "Anlık Oyun Çeviri"
#define MyAppVersion "1.1.1"
#define MyAppVerName "Anlık Oyun Çeviri 1.1.1 BETA"
#define MyAppPublisher "CodeFein Studio"
#define MyAppExeName "AnlikOyunCeviri.exe"
#define MyAppCopyright "Copyright (c) 2026 CodeFein Studio. Tüm hakları saklıdır."

[Setup]
AppId={{A0C7E4F1-9D2E-4B6A-8F3C-5A1E2B3C4D5E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppVerName}
AppPublisher={#MyAppPublisher}
AppCopyright={#MyAppCopyright}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} - Gerçek zamanlı AI oyun çeviri programı
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
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Kısayollar:"

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
; Kullanıcı verisi (ayarlar + çeviri önbelleği) %LOCALAPPDATA%\AnlikOyunCeviri
; altında tutulur. Önbellek kaldırılır; ayarlar ve API anahtarları güvenlik
; gereği korunur (kullanıcı isterse el ile silebilir).
Type: filesandordirs; Name: "{userappdata}\AnlikOyunCeviri\cache"

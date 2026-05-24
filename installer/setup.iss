; =====================================================================
; Mikro Jump Bridge — Inno Setup Kurulum Betiği
; Derlemek için: iscc /DAppVersion=1.2.3 installer\setup.iss
; CI'da dist_build\python_dist\ klasörü önceden hazırlanmış olmalıdır.
; =====================================================================

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

#define MyAppName      "Mikro Jump Bridge"
#define MyAppPublisher "MikroJumpBridge"
#define MyAppURL       "https://mikrojumpbridge.com"
#define MyAppExeName   "baslat.bat"

[Setup]
AppId={{B7A2F3E1-4C5D-4A8B-9F2E-1D3C5E7A9B0F}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\MikroJumpBridge
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Mevcut kurulum varsa otomatik yükselt (veri dosyalarına dokunmaz)
CloseApplications=force
OutputDir=..\dist
OutputBaseFilename=MikroJumpBridge_Kurulum_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
; Yönetici hakları gerektirmez — kullanıcı profili altına kurar
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
WizardSizePercent=120
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName} v{#AppVersion}

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

; -----------------------------------------------------------------------
; DOSYALAR
; -----------------------------------------------------------------------
[Files]
; Python gömülü dağıtımı (CI tarafından dist_build\ altına hazırlanır)
Source: "..\dist_build\python_dist\*"; DestDir: "{app}\python_dist"; Flags: recursesubdirs ignoreversion

; Django uygulamaları
Source: "..\sync_motor\*";      DestDir: "{app}\sync_motor";      Flags: recursesubdirs ignoreversion
Source: "..\hesap_yonetimi\*";  DestDir: "{app}\hesap_yonetimi";  Flags: recursesubdirs ignoreversion
Source: "..\lisans\*";          DestDir: "{app}\lisans";          Flags: recursesubdirs ignoreversion
Source: "..\posta\*";           DestDir: "{app}\posta";           Flags: recursesubdirs ignoreversion
Source: "..\kullanici\*";       DestDir: "{app}\kullanici";       Flags: recursesubdirs ignoreversion
Source: "..\mikro_sync\*";      DestDir: "{app}\mikro_sync";      Flags: recursesubdirs ignoreversion

; Şablonlar (statik dosyalar kurulum sonrası collectstatic ile staticfiles/ altına üretilir)
Source: "..\templates\*";  DestDir: "{app}\templates";  Flags: recursesubdirs ignoreversion

; Kök dosyalar
Source: "..\manage.py";       DestDir: "{app}"; Flags: ignoreversion
Source: "..\pyproject.toml";  DestDir: "{app}"; Flags: ignoreversion
Source: "..\olustur_admin.py"; DestDir: "{app}"; Flags: ignoreversion

; .env.example → .env (yalnızca henüz yoksa yaz — kullanıcı verisini korur)
Source: "..\env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist uninsneverdelete

; Launcher (installer sürümü — bundled Python kullanır)
Source: "baslat_kurulu.bat"; DestDir: "{app}"; DestName: "baslat.bat"; Flags: ignoreversion

[Dirs]
Name: "{app}\logs"

; -----------------------------------------------------------------------
; KISAYOLLAR
; -----------------------------------------------------------------------
[Icons]
Name: "{userdesktop}\{#MyAppName}";  Filename: "{app}\baslat.bat"; WorkingDir: "{app}"
Name: "{group}\{#MyAppName}";        Filename: "{app}\baslat.bat"; WorkingDir: "{app}"
Name: "{group}\Kaldır";              Filename: "{uninstallexe}"

; -----------------------------------------------------------------------
; KURULUM SONRASI ÇALIŞTIR
; -----------------------------------------------------------------------
[Run]
; 1) SECRET_KEY üret (sadece .env'de hâlâ yer tutucu varsa değiştirir)
Filename: "{app}\python_dist\python.exe"; \
  Parameters: "-c ""import re, secrets, pathlib; p=pathlib.Path('.env'); t=p.read_text(encoding='utf-8'); p.write_text(re.sub(r'SECRET_KEY=.*', 'SECRET_KEY='+secrets.token_urlsafe(50), t), encoding='utf-8')"""; \
  WorkingDir: "{app}"; Flags: runhidden waituntilterminated

; 2) Veritabanı migrate
Filename: "{app}\python_dist\python.exe"; \
  Parameters: "manage.py migrate --run-syncdb"; \
  WorkingDir: "{app}"; Flags: runhidden waituntilterminated

; 3) Admin kullanıcısı oluştur (.env'deki ADMIN_KULLANICI/ADMIN_SIFRE'ye göre)
Filename: "{app}\python_dist\python.exe"; \
  Parameters: "olustur_admin.py"; \
  WorkingDir: "{app}"; Flags: runhidden waituntilterminated

; 4) Kurulum bitti — uygulamayı başlat (opsiyonel, kullanıcı onayı ister)
Filename: "{app}\baslat.bat"; \
  Description: "{#MyAppName}'i şimdi başlat"; \
  WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent shellexec

; -----------------------------------------------------------------------
; KALDIRMA — kullanıcı verisine dokunma
; -----------------------------------------------------------------------
[UninstallDelete]
; logs/, db.sqlite3, .env intentionally NOT listed → korunur
Type: filesandordirs; Name: "{app}\python_dist"
Type: filesandordirs; Name: "{app}\sync_motor"
Type: filesandordirs; Name: "{app}\hesap_yonetimi"
Type: filesandordirs; Name: "{app}\lisans"
Type: filesandordirs; Name: "{app}\posta"
Type: filesandordirs; Name: "{app}\kullanici"
Type: filesandordirs; Name: "{app}\mikro_sync"
Type: filesandordirs; Name: "{app}\templates"
Type: filesandordirs; Name: "{app}\static"

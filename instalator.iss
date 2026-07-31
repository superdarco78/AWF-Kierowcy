; AWF KIEROWCY — instalator dla Windows
; Budowany automatycznie na GitHubie, nie trzeba uruchamiac recznie.

#define NazwaApp    "AWF KIEROWCY"
#define WersjaApp   "6.0.1"
#define WydawcaApp  "Straz Akademicka AWF"
#define StronaApp   "https://github.com/superdarco78/AWF-Kierowcy"
#define PlikExe     "AWF-Kierowcy.exe"

[Setup]
AppId={{7C3A9E14-5B2D-4F81-9A6C-2E8D4B1F0C37}
AppName={#NazwaApp}
AppVersion={#WersjaApp}
AppVerName={#NazwaApp} {#WersjaApp}
AppPublisher={#WydawcaApp}
AppPublisherURL={#StronaApp}
AppSupportURL={#StronaApp}

; instalacja bez praw administratora — do katalogu uzytkownika.
; dzieki temu program moze sam podmieniac swoje pliki przy aktualizacji
PrivilegesRequired=lowest
DefaultDirName={autopf}\AWF-Kierowcy
DisableProgramGroupPage=yes
DefaultGroupName={#NazwaApp}

OutputDir=.
OutputBaseFilename=AWF-Kierowcy-Instalator-v{#WersjaApp}
SetupIconFile=ikona.ico
UninstallDisplayIcon={app}\{#PlikExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

; polska wersja jezykowa okna instalatora
ShowLanguageDialog=no

[Languages]
Name: "polski"; MessagesFile: "compiler:Languages\Polish.isl"

[Tasks]
Name: "pulpit"; Description: "Utworz skrot na pulpicie"; \
  GroupDescription: "Skroty:"; Flags: checkedonce
Name: "autostart"; Description: "Uruchamiaj przy starcie systemu"; \
  GroupDescription: "Dyzurka:"; Flags: unchecked

[Files]
Source: "dist\AWF-Kierowcy\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#NazwaApp}"; Filename: "{app}\{#PlikExe}"
Name: "{group}\Odinstaluj {#NazwaApp}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#NazwaApp}"; Filename: "{app}\{#PlikExe}"; Tasks: pulpit
Name: "{userstartup}\{#NazwaApp}"; Filename: "{app}\{#PlikExe}"; Tasks: autostart

[Run]
Filename: "{app}\{#PlikExe}"; \
  Description: "Uruchom {#NazwaApp}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; katalog roboczy programu w dist zostaje po odinstalowaniu — sprzatamy
Type: filesandordirs; Name: "{app}\_internal"

[Messages]
polski.WelcomeLabel2=Program zainstaluje {#NazwaApp} {#WersjaApp} na tym komputerze.%n%nSystem kontroli wjazdu i wyjazdu dla Strazy Akademickiej AWF.%n%nZalecane jest zamkniecie innych programow przed kontynuacja.

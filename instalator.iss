; AWF KIEROWCY — instalator dla Windows
; Numer wersji wpisuje budowanie na GitHubie, nie trzeba go zmieniac recznie.

#define NazwaApp    "AWF KIEROWCY"
#define WersjaApp   "12.0.0"
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
DefaultDirName={userpf}\AWF-Kierowcy
DisableProgramGroupPage=yes
DefaultGroupName={#NazwaApp}

OutputDir=.
OutputBaseFilename=AWF-Kierowcy-Instalator-v{#WersjaApp}
SetupIconFile=ikona.ico
UninstallDisplayIcon={app}\{#PlikExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "polski"; MessagesFile: "compiler:Languages\Polish.isl"

[Tasks]
Name: "pulpit"; Description: "Utworz skrot na pulpicie"; \
  GroupDescription: "Skroty:"; Flags: checkedonce
Name: "obiekty"; Description: "Osobne skroty do zapory i szlabanow"; \
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

; Skroty do poszczegolnych obiektow — kazdy otwiera program od razu na swoim.
; Mozna je przypiac do paska zadan prawym klawiszem.
Name: "{group}\{#NazwaApp} — Zapora"; Filename: "{app}\{#PlikExe}"; \
  Parameters: "--obiekt 1"
Name: "{autodesktop}\Zapora"; Filename: "{app}\{#PlikExe}"; \
  Parameters: "--obiekt 1"; Tasks: obiekty
Name: "{autodesktop}\Szlaban 1"; Filename: "{app}\{#PlikExe}"; \
  Parameters: "--obiekt 2"; Tasks: obiekty
Name: "{autodesktop}\Szlaban 2"; Filename: "{app}\{#PlikExe}"; \
  Parameters: "--obiekt 3"; Tasks: obiekty
Name: "{group}\{#NazwaApp} — Szlaban 1"; Filename: "{app}\{#PlikExe}"; \
  Parameters: "--obiekt 2"
Name: "{group}\{#NazwaApp} — Szlaban 2"; Filename: "{app}\{#PlikExe}"; \
  Parameters: "--obiekt 3"
Name: "{userstartup}\{#NazwaApp}"; Filename: "{app}\{#PlikExe}"; Tasks: autostart

[Run]
Filename: "{app}\{#PlikExe}"; \
  Description: "Uruchom {#NazwaApp}"; \
  Flags: nowait postinstall skipifsilent

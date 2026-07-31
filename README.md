# AWF KIEROWCY

System kontroli wjazdu i wyjazdu dla Straży Akademickiej
Akademii Wychowania Fizycznego Józefa Piłsudskiego w Warszawie.

Obsługuje kilka obiektów różnego rodzaju — zaporę słupkową i szlabany.

---

## Instalacja

Wejdź w **Releases** po prawej stronie i pobierz
**AWF-Kierowcy-Instalator-vX.Y.Z.exe**. Uruchom, kliknij Dalej, gotowe.

Instalator nie wymaga uprawnień administratora — wgrywa program do katalogu
użytkownika, dzięki czemu program może sam podmieniać swoje pliki
przy aktualizacji.

PIN fabryczny: **1234**.

### Bez instalowania

W Releases jest też **AWF-Kierowcy.zip** — wersja przenośna. Rozpakuj
i uruchom `AWF-Kierowcy.exe`.

### Ze źródeł

Kliknij dwa razy **`uruchom.bat`**. Wymaga Pythona; brakującą bibliotekę
Pillow doinstaluje sam.

## Co jest w repozytorium

| Miejsce | Zawartość |
|---|---|
| katalog główny | program i materiały graficzne |
| `wzorzec/` | wzorzec interfejsu w przeglądarce — otwórz `index.html` |
| `dokumenty/` | pięć opisów: interfejs, przełożenie na aplikację, lista kontrolna, aktualizacje, wgrywanie |
| `wersja.json` | numer wersji — **decyduje o samoaktualizacji** |

## Samoaktualizacja

Program po zalogowaniu pyta GitHuba o `wersja.json`. Jeśli jest nowsza wersja,
pokazuje okno z opisem zmian i po zgodzie sam się aktualizuje.

Numer wersji widnieje w prawym górnym rogu programu.

**Nie edytujesz numeru ręcznie** — liczy się sam z opisu, który wpisujesz
przy wgrywaniu plików:

| Opis wgrania | Numer |
|---|---|
| `Poprawka literówki` | 6.0.1 → 6.0.2 |
| `Nowe: kolejka pojazdów` | 6.0.2 → 6.1.0 |
| `PRZELOM: zmiana formatu bazy` | 6.1.0 → 7.0.0 |

Szczegóły w `dokumenty/05-JAK-WGRYWAC.md`.

## Scena z prawdziwego zdjęcia

Podgląd zapory to fotografia wjazdu, a słupki są wycięte z tego samego zdjęcia.
Każda klatka animacji to ten sam wycinek, tylko krótszy.

## Barwy i znak

Kolory pobrane wprost z godła: zieleń **#006341**, złoto **#b9975b**.
W trybie ciemnym zieleń rozjaśniona do **#00a86b**, bo oryginalna ma na ciemnym
tle kontrast 2,4 przy wymaganych 4,5.

---

## Dane osobowe

Numery telefonów **nie trafiają do repozytorium**. Baza leży
w `%APPDATA%\AWF-Kierowcy\baza.json` na komputerze dyżurki i jest wpisana
do `.gitignore`.

W repozytorium jest sam program i sześciu wymyślonych kierowców.
Dzięki temu repozytorium może być publiczne — a musi, bo program pobiera
`wersja.json` bez logowania.

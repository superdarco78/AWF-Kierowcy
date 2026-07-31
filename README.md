# AWF KIEROWCY

Kontrola wjazdu i wyjazdu — Straż Akademicka AWF w Warszawie.
Obsługuje zaporę słupkową i szlabany.

## Pobranie gotowego programu

Zakładka **Releases** po prawej → pobierz
**AWF-Kierowcy-Instalator-vX.Y.Z.exe** i uruchom.

PIN fabryczny: **1234**

## Uruchomienie ze źródeł

Kliknij dwa razy `uruchom.bat`. Wymaga Pythona.

## Samoaktualizacja

Program przy uruchomieniu sprawdza `wersja.json` w tym repozytorium.
Gdy jest nowsza wersja, pokazuje okno z opisem zmian i sam się aktualizuje.

Numer wersji widnieje w prawym górnym rogu programu.

## Wgrywanie zmian

Wgraj zmienione pliki i wpisz opis. Numer wersji policzy się sam:

| Opis wgrania | Numer |
|---|---|
| `Poprawka literówki` | 6.0.1 → 6.0.2 |
| `Nowe: kolejka pojazdów` | 6.0.2 → 6.1.0 |
| `PRZELOM: zmiana bazy` | 6.1.0 → 7.0.0 |

Budowanie zbuduje instalator, opublikuje wydanie i zapisze `wersja.json`.

## Ta sama baza na kilku komputerach

**Ustawienia → Gdzie trzymać bazę → Wskaż katalog w OneDrive**

Program przeniesie tam bazę. Na drugim komputerze instalujesz program
i wskazujesz **ten sam katalog** — numery, harmonogramy i historia pojawią się
same. OneDrive synchronizuje plik, program go czyta.

Nic nie trzeba wpisywać drugi raz.

Do przeniesienia jednorazowego są też przyciski **Zapisz kopię bazy**
i **Wczytaj kopię** — plik można przenieść pendrivem.

## Dane osobowe

Numery telefonów **nie trafiają do repozytorium**. Baza leży w katalogu
użytkownika albo w OneDrive — tam, gdzie wskażesz.

To repozytorium jest publiczne, więc trzymanie w nim prawdziwych numerów
oznaczałoby, że zobaczy je każdy w internecie.

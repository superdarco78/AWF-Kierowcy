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

**Na ekranie logowania program aktualizuje się sam.** Sprawdza `wersja.json`
w tym repozytorium jeszcze przed wpisaniem PIN-u, pobiera nową wersję,
podmienia pliki i wraca — bez pytania i bez klikania. Postęp widać w rogu
ekranu logowania. Po zalogowaniu wita zielony pasek „Zaktualizowano do
wersji X".

W czasie służby, gdy ktoś jest już zalogowany, program **nie zamyka się sam**.
Wtedy pokazuje okno z opisem zmian i czeka na decyzję.

Numer wersji widnieje w prawym górnym rogu programu, a przed zalogowaniem
w prawym dolnym rogu ekranu PIN-u.

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

## Zdjęcia wbudowane w kod

Godło, logo poziome i tło ekranu logowania siedzą w pliku
`zasoby_wbudowane.py` zamienione na tekst. Program spakowany PyInstallerem
to nie folder z plikami — każdy dołączony plik trzeba wpisać na listę
w pliku budowania i wystarczy jedno przeoczenie, żeby program działał
bez zdjęcia.

Kolejność szukania: **najpierw plik obok programu, potem wersja z kodu.**
Żeby podmienić tło, wystarczy położyć nowy `logowanie-tlo.jpg` w katalogu
programu — nie trzeba niczego przebudowywać.

Pliki budowania dołączają teraz wszystkie obrazy same (`*.png`, `*.jpg`,
`*.ico`, `*.json`), więc nowa grafika nie wymaga dopisywania jej z nazwy.

## Dane osobowe

Numery telefonów **nie trafiają do repozytorium**. Baza leży w katalogu
użytkownika albo w OneDrive — tam, gdzie wskażesz.

To repozytorium jest publiczne, więc trzymanie w nim prawdziwych numerów
oznaczałoby, że zobaczy je każdy w internecie.

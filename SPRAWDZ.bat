@echo off
chcp 65001 >nul
title AWF KIEROWCY - sprawdzenie plikow
cd /d "%~dp0"
set "WYNIK=%~dp0sprawdzenie.txt"

> "%WYNIK%" echo ================================================
>>"%WYNIK%" echo   AWF KIEROWCY - co naprawde lezy w tym folderze
>>"%WYNIK%" echo ================================================
>>"%WYNIK%" echo.
>>"%WYNIK%" echo Folder: %~dp0
>>"%WYNIK%" echo Data:   %date% %time%
>>"%WYNIK%" echo.
>>"%WYNIK%" echo --- pliki, ktore musza byc ---

for %%F in (awf_kierowcy.py zasoby_wbudowane.py aktualizacje.py okno_aktualizacji.py logowanie-tlo.jpg godlo-awf.png) do (
    if exist "%%F" (
        >>"%WYNIK%" echo JEST   %%~zF bajtow   %%F
    ) else (
        >>"%WYNIK%" echo BRAK   %%F
    )
)

>>"%WYNIK%" echo.
>>"%WYNIK%" echo --- czy w kodzie sa nowe poprawki ---

findstr /C:"godlo_okragle" awf_kierowcy.py >nul 2>&1
if errorlevel 1 (>>"%WYNIK%" echo NIE MA  okragle godlo bez zielonego kwadratu) else (>>"%WYNIK%" echo JEST    okragle godlo bez zielonego kwadratu)

findstr /C:"zasoby_wbudowane" awf_kierowcy.py >nul 2>&1
if errorlevel 1 (>>"%WYNIK%" echo NIE MA  zdjecia wbudowane w kod) else (>>"%WYNIK%" echo JEST    zdjecia wbudowane w kod)

findstr /C:"_cicha_aktualizacja" awf_kierowcy.py >nul 2>&1
if errorlevel 1 (>>"%WYNIK%" echo NIE MA  aktualizacja bez pytania) else (>>"%WYNIK%" echo JEST    aktualizacja bez pytania)

findstr /C:"036744" awf_kierowcy.py >nul 2>&1
if errorlevel 1 (>>"%WYNIK%" echo NIE MA  barwy uczelni 036744) else (>>"%WYNIK%" echo JEST    barwy uczelni 036744)

findstr /C:"ttk.Progressbar" okno_aktualizacji.py >nul 2>&1
if errorlevel 1 (>>"%WYNIK%" echo JEST    zielony pasek postepu) else (>>"%WYNIK%" echo NIE MA  zielony pasek - dalej systemowy bialy)

>>"%WYNIK%" echo.
>>"%WYNIK%" echo --- numer wersji w kodzie ---
findstr /R /C:"^VER = " awf_kierowcy.py >>"%WYNIK%" 2>&1

>>"%WYNIK%" echo.
>>"%WYNIK%" echo --- wszystkie pliki w folderze ---
dir /b >>"%WYNIK%" 2>&1

>>"%WYNIK%" echo.
>>"%WYNIK%" echo ================================================
>>"%WYNIK%" echo Zrob zdjecie tego okna albo wklej tresc.
>>"%WYNIK%" echo ================================================

notepad "%WYNIK%"

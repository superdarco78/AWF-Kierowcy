@echo off
chcp 65001 >nul
title AWF KIEROWCY - budowanie programu
cd /d "%~dp0"

echo.
echo ================================================
echo   AWF KIEROWCY - budowanie programu .exe
echo ================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Nie znaleziono Pythona.
    echo.
    echo Pobierz z https://www.python.org/downloads/
    echo WAZNE: przy instalacji zaznacz "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/4] Sprawdzam narzedzia...
python -m pip install --quiet --upgrade pip pyinstaller pillow
if errorlevel 1 (
    echo [BLAD] Nie udalo sie zainstalowac narzedzi.
    pause
    exit /b 1
)
echo       gotowe.
echo.

echo [2/4] Buduje program... ^(to potrwa 1-2 minuty^)
python -m PyInstaller --onedir --windowed --clean --noupx ^
  --name "AWF-Kierowcy" ^
  --icon ikona.ico ^
  --manifest manifest.xml ^
  --hidden-import tlo_wbudowane ^
  --add-data "ikona.ico;." ^
  --add-data "godlo-awf.png;." ^
  --add-data "logowanie-tlo.jpg;." ^
  --add-data "logo-awf.png;." ^
  --add-data "kiosk-tlo.jpg;." ^
  --add-data "kiosk-uklad.json;." ^
  --add-data "wersja-programu.txt;." ^
  --add-data "kiosk-korpus1.png;." ^
  --add-data "kiosk-korpus2.png;." ^
  --add-data "kiosk-korpus3.png;." ^
  --add-data "kiosk-korpus4.png;." ^
  --add-data "kiosk-plyta1.png;." ^
  --add-data "kiosk-plyta2.png;." ^
  --add-data "kiosk-plyta3.png;." ^
  --add-data "kiosk-plyta4.png;." ^
  --log-level WARN ^
  awf_kierowcy.py
if errorlevel 1 (
    echo.
    echo [BLAD] Budowanie sie nie udalo. Przewin w gore i przeczytaj komunikat.
    pause
    exit /b 1
)
echo       gotowe.
echo.

echo [3/4] Sprawdzam wynik...
if not exist "dist\AWF-Kierowcy\AWF-Kierowcy.exe" (
    echo [BLAD] Nie powstal plik AWF-Kierowcy.exe
    pause
    exit /b 1
)
echo       program jest w: dist\AWF-Kierowcy\AWF-Kierowcy.exe
echo.

echo [4/4] Buduje instalator...
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
    "%ISCC%" instalator.iss
    if errorlevel 1 (
        echo       [uwaga] Instalator sie nie zbudowal, ale program dziala.
    ) else (
        echo       instalator gotowy w tym katalogu.
    )
) else (
    echo       [pominieto] Nie znaleziono Inno Setup.
    echo.
    echo       Instalator nie jest konieczny - program juz dziala.
    echo       Jesli chcesz instalator, pobierz Inno Setup:
    echo       https://jrsoftware.org/isdl.php
)

echo.
echo ================================================
echo   GOTOWE
echo ================================================
echo.
echo   Program:    dist\AWF-Kierowcy\AWF-Kierowcy.exe
echo   PIN:        1234
echo.
echo   Caly folder "dist\AWF-Kierowcy" mozesz skopiowac
echo   na dowolny komputer - dziala bez instalowania.
echo.
choice /C TN /M "Uruchomic program teraz? [T/N]"
if errorlevel 2 goto koniec
start "" "dist\AWF-Kierowcy\AWF-Kierowcy.exe"

:koniec
echo.
pause

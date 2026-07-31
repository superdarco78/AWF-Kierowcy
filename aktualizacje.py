"""
WARTA AWF — samoaktualizacja z GitHuba.

Zasada dzialania:

1. Program przy starcie pyta GitHuba o najnowsze wydanie.
2. Jesli jest nowsze niz zainstalowane, pokazuje okno z opisem zmian.
3. Po zgodzie pobiera paczke, sprawdza sume kontrolna i rozpakowuje do katalogu
   tymczasowego.
4. Uruchamia maly program pomocniczy, ktory czeka az glowna aplikacja sie zamknie,
   podmienia pliki i uruchamia ja ponownie.

Punkt czwarty jest konieczny, bo Windows nie pozwala nadpisac pliku programu,
ktory wlasnie dziala. Podmiany musi dokonac ktos z zewnatrz.

Wymagania po stronie repozytorium: kazde wydanie ma zalacznik `WARTA-AWF.zip`
oraz plik `wersja.json` w glownym katalogu galezi main.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
import zipfile

REPO = "superdarco78/AWF-Kierowcy"
ADRES_WERSJI = f"https://raw.githubusercontent.com/{REPO}/main/wersja.json"
LIMIT_S = 8


# --------------------------------------------------------------------------
# porownywanie wersji
# --------------------------------------------------------------------------

def rozbij(wersja):
    """'6.10.2' -> (6, 10, 2). Czesci nieliczbowe traktuje jak zero."""
    czesci = []
    for kawalek in str(wersja).strip().lstrip("vV").split("."):
        cyfry = "".join(z for z in kawalek if z.isdigit())
        czesci.append(int(cyfry) if cyfry else 0)
    while len(czesci) < 3:
        czesci.append(0)
    return tuple(czesci[:3])


def nowsza(kandydat, obecna):
    """Czy kandydat jest nowszy od obecnej."""
    return rozbij(kandydat) > rozbij(obecna)


# --------------------------------------------------------------------------
# sprawdzanie dostepnosci
# --------------------------------------------------------------------------

def stan_serwera(obecna_wersja, adres=None):
    """Pyta serwer i zwraca (rodzaj, dane).

    rodzaj:
      "jest"      — jest nowsza wersja, dane to slownik z opisem
      "aktualna"  — masz najnowsza, dane to numer wersji na serwerze
      "brak"      — nie udalo sie polaczyc, dane to opis problemu
    """
    # adres czytamy przy kazdym wywolaniu, nie raz przy starcie —
    # dzieki temu da sie go podmienic bez przebudowywania programu
    adres = adres or ADRES_WERSJI
    try:
        zadanie = urllib.request.Request(
            adres, headers={"User-Agent": "AWF-Kierowcy"})
        with urllib.request.urlopen(zadanie, timeout=LIMIT_S) as odp:
            dane = json.loads(odp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return "brak", f"serwer odpowiedzial bledem {e.code}"
    except (urllib.error.URLError, OSError):
        return "brak", "brak polaczenia z internetem"
    except (ValueError, json.JSONDecodeError):
        return "brak", "plik wersji jest uszkodzony"

    if not isinstance(dane, dict) or "wersja" not in dane:
        return "brak", "plik wersji nie ma numeru"
    if not nowsza(dane["wersja"], obecna_wersja):
        return "aktualna", str(dane["wersja"])
    return "jest", {
        "wersja": str(dane["wersja"]),
        "opis": dane.get("opis", ""),
        "paczka": dane.get("paczka", ""),
        "suma": dane.get("suma", ""),
        "wymagana": bool(dane.get("wymagana", False)),
    }


def sprawdz(obecna_wersja, adres=None):
    """Zwraca slownik z opisem aktualizacji albo None. Nigdy nie rzuca
    wyjatkiem — brak internetu nie moze przeszkodzic w uruchomieniu."""
    rodzaj, dane = stan_serwera(obecna_wersja, adres)
    return dane if rodzaj == "jest" else None


def historia_wersji(limit=20, adres=None):
    """Lista wydan z GitHuba: numer, data i opis zmian.

    Zwraca liste slownikow albo pusta liste, gdy nie udalo sie polaczyc.
    Nigdy nie rzuca wyjatkiem.
    """
    adres = adres or f"https://api.github.com/repos/{REPO}/releases?per_page={limit}"
    try:
        zadanie = urllib.request.Request(
            adres, headers={"User-Agent": "AWF-Kierowcy",
                            "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(zadanie, timeout=LIMIT_S) as odp:
            dane = json.loads(odp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return []

    if not isinstance(dane, list):
        return []
    out = []
    for w in dane:
        znacznik = str(w.get("tag_name", "")).lstrip("vV")
        if not znacznik:
            continue
        out.append({
            "wersja": znacznik,
            "data": str(w.get("published_at", ""))[:10],
            "opis": (w.get("body") or "").strip(),
        })
    out.sort(key=lambda x: rozbij(x["wersja"]), reverse=True)
    return out


def sprawdz_w_tle(obecna_wersja, gdy_jest, adres=None):
    """Sprawdza w osobnym watku, zeby okno programu nie stalo.

    `gdy_jest` dostanie slownik z opisem aktualizacji. Wywolanie trzeba
    przekazac do watku glownego przez `after`, bo tkinter nie znosi
    grzebania w oknach z innego watku.
    """
    def robota():
        wynik = sprawdz(obecna_wersja, adres)
        if wynik:
            gdy_jest(wynik)

    watek = threading.Thread(target=robota, daemon=True)
    watek.start()
    return watek


# --------------------------------------------------------------------------
# pobieranie
# --------------------------------------------------------------------------

def suma_pliku(sciezka):
    h = hashlib.sha256()
    with open(sciezka, "rb") as f:
        for kawalek in iter(lambda: f.read(65536), b""):
            h.update(kawalek)
    return h.hexdigest()


def pobierz(info, postep=None):
    """Pobiera paczke do katalogu tymczasowego i sprawdza sume kontrolna.

    `postep` dostaje liczbe od 0 do 1. Zwraca sciezke do pliku zip.
    Rzuca wyjatkiem, gdy pobieranie sie nie uda albo suma sie nie zgadza —
    lepiej przerwac niz podmienic program na uszkodzony.
    """
    katalog = tempfile.mkdtemp(prefix="warta-akt-")
    plik = os.path.join(katalog, "paczka.zip")

    zadanie = urllib.request.Request(
        info["paczka"], headers={"User-Agent": "WARTA-AWF"})
    with urllib.request.urlopen(zadanie, timeout=60) as odp:
        calosc = int(odp.headers.get("Content-Length") or 0)
        pobrane = 0
        with open(plik, "wb") as f:
            while True:
                kawalek = odp.read(65536)
                if not kawalek:
                    break
                f.write(kawalek)
                pobrane += len(kawalek)
                if postep and calosc:
                    postep(min(1.0, pobrane / calosc))

    if info.get("suma"):
        policzona = suma_pliku(plik)
        if policzona.lower() != info["suma"].lower():
            shutil.rmtree(katalog, ignore_errors=True)
            raise ValueError(
                "suma kontrolna sie nie zgadza — paczka moze byc uszkodzona")

    return plik


def rozpakuj(plik_zip):
    """Rozpakowuje paczke obok niej i zwraca katalog z plikami.

    Odrzuca sciezki wychodzace poza katalog docelowy — zlosliwie spreparowany
    zip potrafi w ten sposob nadpisac pliki systemowe.
    """
    katalog = os.path.join(os.path.dirname(plik_zip), "nowe")
    os.makedirs(katalog, exist_ok=True)
    with zipfile.ZipFile(plik_zip) as z:
        for wpis in z.namelist():
            cel = os.path.realpath(os.path.join(katalog, wpis))
            if not cel.startswith(os.path.realpath(katalog)):
                raise ValueError(f"paczka zawiera podejrzana sciezke: {wpis}")
        z.extractall(katalog)

    # jesli zip ma jeden katalog na wierzchu, wchodzimy do srodka
    wpisy = os.listdir(katalog)
    if len(wpisy) == 1 and os.path.isdir(os.path.join(katalog, wpisy[0])):
        katalog = os.path.join(katalog, wpisy[0])
    return katalog


# --------------------------------------------------------------------------
# podmiana plikow
# --------------------------------------------------------------------------

POMOCNIK = r"""@echo off
chcp 65001 >nul
title AWF KIEROWCY - aktualizacja

echo Czekam na zamkniecie programu...
:czekaj
tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto czekaj
)

echo Zapisuje kopie poprzedniej wersji...
if exist "{kopia}" rmdir /s /q "{kopia}"
mkdir "{kopia}" 2>nul
xcopy "{docelowy}\*" "{kopia}\" /E /I /Y /Q >nul

echo Podmieniam pliki...
xcopy "{zrodlo}\*" "{docelowy}\" /E /I /Y /Q
if errorlevel 1 (
    echo.
    echo Podmiana sie nie udala - przywracam poprzednia wersje.
    xcopy "{kopia}\*" "{docelowy}\" /E /I /Y /Q >nul
    echo Przywrocono poprzednia wersje.
    pause
    exit /b 1
)

echo Uruchamiam program...

rem Szukamy pliku programu zamiast zakladac sciezke.
set "PROGRAM="
if exist "{docelowy}\{nazwa_exe}" set "PROGRAM={docelowy}\{nazwa_exe}"

if not defined PROGRAM (
    for %%P in ("{docelowy}\*.exe") do (
        if not defined PROGRAM set "PROGRAM=%%~fP"
    )
)

if defined PROGRAM (
    start "" /D "{docelowy}" "%PROGRAM%"
) else (
    rem Uruchomienie ze zrodel - wtedy potrzebny jest Python.
    if exist "{docelowy}\{nazwa_skryptu}" (
        start "" /D "{docelowy}" cmd /c "{polecenie_zrodel}"
    ) else (
        echo.
        echo Nie znaleziono programu w:
        echo   {docelowy}
        echo.
        echo Pliki zostaly podmienione poprawnie - uruchom program
        echo recznie z tego katalogu albo ze skrotu na pulpicie.
        echo.
        echo Okno zamknie sie za 15 sekund.
        timeout /t 15 /nobreak >nul
        exit /b 1
    )
)

timeout /t 2 /nobreak >nul
rmdir /s /q "{tymczasowy}" 2>nul
exit
"""


def nazwa_programu():
    """Nazwa pliku programu — po spakowaniu PyInstallerem to plik exe."""
    if getattr(sys, "frozen", False):
        return os.path.basename(sys.executable)
    return "AWF-Kierowcy.exe"


def przygotuj_pomocnika(katalog_nowych, katalog_programu, sciezka_programu=None):
    """Tworzy plik wsadowy, ktory podmieni pliki po zamknieciu programu.

    Plik sam szuka programu w katalogu docelowym zamiast zakladac sciezke.
    Po podmianie plikow nazwa albo polozenie moga sie roznic od tego,
    co bylo przed aktualizacja — a wtedy program by sie nie uruchomil.
    """
    tymczasowy = os.path.dirname(katalog_nowych)
    plik = os.path.join(tymczasowy, "aktualizuj.bat")
    skrypt = os.path.basename(os.path.abspath(sys.argv[0])) or "awf_kierowcy.py"
    tresc = POMOCNIK.format(
        pid=os.getpid(),
        zrodlo=katalog_nowych,
        docelowy=katalog_programu,
        kopia=os.path.join(tymczasowy, "kopia"),
        nazwa_exe=nazwa_programu(),
        nazwa_skryptu=skrypt,
        polecenie_zrodel='"%s" "%s"' % (sys.executable, skrypt),
        tymczasowy=tymczasowy,
    )
    with open(plik, "w", encoding="utf-8") as f:
        f.write(tresc)
    return plik


def uruchom_pomocnika(plik_bat):
    """Odpala pomocnika i zwraca sterowanie. Program powinien zaraz sie zamknac."""
    subprocess.Popen(
        ["cmd", "/c", "start", "", plik_bat],
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        close_fds=True,
    )


def katalog_programu():
    """Gdzie leza pliki programu — inaczej przy uruchomieniu ze zrodel,
    inaczej po spakowaniu PyInstallerem."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def polecenie_startu():
    """Jak uruchomic program po podmianie plikow.

    Po spakowaniu PyInstallerem to zwykly plik exe. Przy uruchomieniu
    ze zrodel trzeba wywolac Pythona z nazwa skryptu — inaczej `start`
    probowalby otworzyc plik .py edytorem.
    """
    if getattr(sys, "frozen", False):
        return '"%s"' % sys.executable
    skrypt = os.path.basename(os.path.abspath(sys.argv[0]))
    return '"%s" "%s"' % (sys.executable, skrypt)


def sciezka_programu():
    """zachowane dla zgodnosci ze starszym kodem"""
    return polecenie_startu()

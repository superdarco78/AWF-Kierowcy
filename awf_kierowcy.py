"""
AWF KIEROWCY — kontrola wjazdu i wyjazdu
Straz Akademicka AWF Jozefa Pilsudskiego w Warszawie

Przepisane ze wzorca interfejsu. Wszystkie kolory siedza w slowniku BARWY,
zeby zmiana motywu byla jedna podmiana, a nie szukaniem po pliku.
"""

import json
import os
import sys
import hashlib
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import (Image, ImageTk, ImageDraw, ImageFilter,
                 ImageFont, ImageEnhance)
except ImportError:
    print("Brakuje biblioteki Pillow. Uruchom: pip install pillow")
    sys.exit(1)

VER = "12.0.0"


def wersja_programu():
    """Numer wersji pokazywany w programie.

    Bierzemy go z pliku wersja-programu.txt lezacego obok programu.
    Powod: budowanie na GitHubie nadpisuje stala VER wlasnym numerem,
    wiec wpisanie czegokolwiek w kodzie nie ma znaczenia. Zwykly plik
    tekstowy nie jest przez nikogo ruszany — podmienia sie razem
    z reszta paczki i pokazuje dokladnie to, co w nim jest.

    Gdy pliku nie ma, zostaje numer ze stalej VER.
    """
    plik = zasob("wersja-programu.txt")
    if plik:
        try:
            with open(plik, encoding="utf-8") as f:
                napis = f.read().strip().lstrip("vV")
            if napis and napis[0].isdigit():
                return napis
        except OSError:
            pass
    return VER
NAZWA = "AWF KIEROWCY"
PODTYTUL = "Kontrola wjazdu i wyjazdu"

DNI = ["pn", "wt", "sr", "cz", "pt", "so", "nd"]
DNI_PELNE = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek",
             "sobota", "niedziela"]


# ==========================================================================
# barwy — dwa komplety, jak w bloku :root i body.jasny we wzorcu
# ==========================================================================

# Obie palety wyprowadzone z dwoch barw uczelni: zielen #036744 i zloto
# #b9975b. Tla to ta sama zielen zmieszana z czernia, napisy — z biela.
#
# Zielen uczelni jest ciemna, wiec sluzy jako WYPELNIENIE z bialym napisem
# (kontrast 6,9). Jako napis na ciemnym tle mialaby 2,6, czyli bylaby
# nieczytelna — do tego jest "akcentTekst", ta sama zielen rozjasniona.

CIEMNY = {
    "tlo": "#001309", "tlo2": "#011c12", "tlo3": "#01291b", "linia": "#023c27",
    "tekst": "#ebf3f0", "tekst2": "#b3d1c7", "przygasz": "#86b6a5",
    "akcent": "#036744", "akcent2": "#024a31", "akcentTekst": "#599b84",
    "zloto": "#b9975b", "zloto2": "#856d42",
    "ok": "#599b84", "uwaga": "#b9975b", "alarm": "#ff6b6b",
    "naAkcencie": "#ffffff", "naPanelu": "#ebf3f0",
    "panel": (1, 28, 18, 194), "panelRamka": (185, 151, 91, 56),
    "scenaTlo": "#000805", "welon": 0,
}

JASNY = {
    "tlo": "#f4f8f7", "tlo2": "#ffffff", "tlo3": "#e6f0ec", "linia": "#c8ded6",
    "tekst": "#024830", "tekst2": "#036140", "przygasz": "#2f7a61",
    "akcent": "#036744", "akcent2": "#024d33", "akcentTekst": "#036744",
    "zloto": "#6b5835", "zloto2": "#b9975b",
    "ok": "#036744", "uwaga": "#6b5835", "alarm": "#b32626",
    "naAkcencie": "#ffffff", "naPanelu": "#024830",
    "panel": (255, 255, 255, 219), "panelRamka": (3, 103, 68, 56),
    "scenaTlo": "#e1ede9", "welon": 56,
}

# ==========================================================================
# style graficzne — dwanascie palet do wyboru w Ustawieniach
#
# Kazdy styl to komplet barw nadpisujacy palete bazowa. Numer 3 to barwy
# uczelni i on jest domyslny. Style jasne maja "welon" wiekszy od zera —
# po tym program poznaje, ze rysuje na jasnym tle.
# ==========================================================================

STYLE = {
    1: ("Szkło", dict(CIEMNY)),
    2: ("Grafit", dict(CIEMNY, tlo="#141614", tlo2="#1c1e1d", tlo3="#2a2d2b",
                       linia="#3c403e", tekst="#f2f2f0", tekst2="#c8ccc9",
                       przygasz="#9aa09d", zloto="#d6bd8a", zloto2="#a48a5c",
                       naPanelu="#f2f2f0", scenaTlo="#0d0f0e",
                       panel=(20, 22, 21, 200), panelRamka=(214, 189, 138, 60))),
    3: ("Zieleń uczelni", dict(CIEMNY)),
    4: ("Mleczne szkło", dict(JASNY)),
    5: ("Papier", dict(JASNY, tlo="#fdfdfc", tlo2="#ffffff", tlo3="#f4f3ef",
                       linia="#dedcd6", tekst="#1a1a18", tekst2="#3f3f3a",
                       przygasz="#6b6b64", akcent="#036744", akcent2="#024a31",
                       zloto="#7a6129", zloto2="#a68a4e", ok="#0d5730",
                       uwaga="#7a5300", alarm="#8c1d16", naPanelu="#1a1a18",
                       panel=(255, 255, 255, 235), panelRamka=(26, 26, 24, 60),
                       scenaTlo="#eceae4", welon=64)),
    6: ("Kontrast", dict(CIEMNY, tlo="#000000", tlo2="#0c0c0c", tlo3="#1a1a1a",
                         linia="#3a3a3a", tekst="#ffffff", tekst2="#e0e0e0",
                         przygasz="#b8b8b8", akcent="#005c3c", akcent2="#00432c",
                         zloto="#ffd600", zloto2="#c7a800", ok="#00e676",
                         uwaga="#ffd600", alarm="#ff5252", naPanelu="#ffffff",
                         panel=(0, 0, 0, 225), panelRamka=(255, 214, 0, 90),
                         scenaTlo="#000000")),
    7: ("Pergamin", dict(JASNY, tlo="#f7f2e6", tlo2="#fcf9f0", tlo3="#efe8d6",
                         linia="#ddd2b8", tekst="#3a3122", tekst2="#5c5240",
                         przygasz="#7d7059", akcent="#3f6b2e", akcent2="#2e5120",
                         zloto="#7a6129", zloto2="#a8874a", ok="#3f6b2e",
                         uwaga="#8a6a12", alarm="#8c3a16", naPanelu="#3a3122",
                         panel=(252, 249, 240, 235), panelRamka=(122, 97, 41, 70),
                         scenaTlo="#e9e0cb", welon=52)),
    8: ("Stal", dict(JASNY, tlo="#eef1f3", tlo2="#ffffff", tlo3="#e0e7ec",
                     linia="#c6d1d8", tekst="#16232c", tekst2="#37505f",
                     przygasz="#5b7383", akcent="#26535f", akcent2="#1a3d47",
                     zloto="#6a7f8c", zloto2="#8aa2b4", ok="#0f6b46",
                     uwaga="#8a6206", alarm="#a32a20", naPanelu="#16232c",
                     panel=(255, 255, 255, 232), panelRamka=(38, 83, 95, 70),
                     scenaTlo="#d7e0e6", welon=58)),
    9: ("Noc", dict(CIEMNY, tlo="#070a12", tlo2="#0e1420", tlo3="#182034",
                    linia="#2a3855", tekst="#e8eef8", tekst2="#c0cde0",
                    przygasz="#93a5c0", akcent="#1e3a68", akcent2="#152a4d",
                    zloto="#8fb0e8", zloto2="#6b8ec4", ok="#4fd6a8",
                    uwaga="#f0c669", alarm="#ff8ea0", naPanelu="#e8eef8",
                    panel=(14, 20, 32, 205), panelRamka=(143, 176, 232, 70),
                    scenaTlo="#050810")),
    10: ("Zieleń jasna", dict(JASNY, tlo="#f4f8f7", tlo2="#ffffff",
                              tlo3="#e4efea", linia="#c3ded2")),
    11: ("Marmur", dict(JASNY, tlo="#faf9f6", tlo2="#ffffff", tlo3="#f0eee8",
                        linia="#dcd8cf", tekst="#22201b", tekst2="#464339",
                        przygasz="#6d6857", akcent="#2f6b41", akcent2="#22502f",
                        zloto="#8a7340", zloto2="#b09a68", ok="#2f6b41",
                        uwaga="#8a6a12", alarm="#9c2b20", naPanelu="#22201b",
                        panel=(255, 255, 255, 235), panelRamka=(138, 115, 64, 70),
                        scenaTlo="#e8e5dd", welon=54)),
    12: ("Złoto na czerni", dict(CIEMNY, tlo="#0a0908", tlo2="#151310",
                                 tlo3="#221e16", linia="#3d3628",
                                 tekst="#f4efe3", tekst2="#d8cfba",
                                 przygasz="#a89b82", akcent="#4a3f28",
                                 akcent2="#332c1c", zloto="#d8b871",
                                 zloto2="#a88c4e", ok="#7ed6a0",
                                 uwaga="#e8c46a", alarm="#ff9a8e",
                                 naPanelu="#f4efe3",
                                 panel=(21, 19, 16, 215),
                                 panelRamka=(216, 184, 113, 80),
                                 scenaTlo="#080706")),
}

B = dict(CIEMNY)          # biezaca paleta


def zastosuj_motyw(jasny, styl=None):
    """Ustawia biezaca palete.

    Gdy podano numer stylu, bierzemy go z tablicy STYLE. Motyw jasny/ciemny
    zostaje dla zgodnosci ze starszymi ustawieniami — style same okreslaja,
    czy sa jasne, przez klucz "welon".
    """
    B.clear()
    if styl and styl in STYLE:
        B.update(STYLE[styl][1])
        return
    B.update(JASNY if jasny else CIEMNY)


# ==========================================================================
# pliki i dane
# ==========================================================================

def zasob(nazwa):
    """Sciezka do pliku dolaczonego do programu — inaczej ze zrodel,
    inaczej po spakowaniu PyInstallerem."""
    if hasattr(sys, "_MEIPASS"):
        p = os.path.join(sys._MEIPASS, nazwa)
        if os.path.exists(p):
            return p
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), nazwa)
    return p if os.path.exists(p) else None


def juz_dziala():
    """Czy program juz jest uruchomiony.

    Na Windows pytamy system o nazwany znacznik — pierwszy program go
    zaklada, drugi dostaje informacje, ze taki juz jest. Poza Windows
    pilnujemy tego plikiem z numerem procesu.

    Dwa okna naraz to nie tylko balagan: obie kopie pisza do tego samego
    pliku bazy i ta, ktora zapisze pozniej, kasuje prace tej pierwszej.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            znacznik = ctypes.windll.kernel32.CreateMutexW(
                None, False, "AWF-KIEROWCY-jedno-uruchomienie")
            global _ZNACZNIK
            _ZNACZNIK = znacznik              # trzymamy, zeby nie zniknal
            return ctypes.windll.kernel32.GetLastError() == 183   # JUZ_ISTNIEJE
        except OSError:
            return False
    plik = os.path.join(katalog_domyslny(), "dziala.pid")
    try:
        if os.path.exists(plik):
            with open(plik, encoding="utf-8") as f:
                pid = int(f.read().strip() or 0)
            if pid and pid != os.getpid():
                try:
                    os.kill(pid, 0)
                    return True
                except OSError:
                    pass
        with open(plik, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except (OSError, ValueError):
        return False
    return False


def obiekt_z_polecenia():
    """Numer obiektu podany przy uruchomieniu: --obiekt 2.

    Dzieki temu skrot na pulpicie albo w pasku zadan moze otwierac program
    od razu na zaporze, szlabanie 1 albo szlabanie 2.
    """
    for i, arg in enumerate(sys.argv):
        if arg in ("--obiekt", "-o") and i + 1 < len(sys.argv):
            try:
                return max(0, int(sys.argv[i + 1]) - 1)
            except ValueError:
                return 0
        if arg.startswith("--obiekt="):
            try:
                return max(0, int(arg.split("=", 1)[1]) - 1)
            except ValueError:
                return 0
    return 0


def katalog_domyslny():
    baza = os.environ.get("APPDATA") or os.path.expanduser("~")
    kat = os.path.join(baza, "AWF-Kierowcy")
    os.makedirs(kat, exist_ok=True)
    return kat


def plik_wskazania():
    """Maly plik obok ustawien, mowiacy gdzie trzymac baze."""
    return os.path.join(katalog_domyslny(), "gdzie-baza.txt")


def katalog_danych():
    """Katalog z baza. Domyslnie w ustawieniach uzytkownika, ale mozna
    wskazac inny — na przyklad w OneDrive, zeby ta sama baza byla
    widoczna na kilku komputerach."""
    try:
        with open(plik_wskazania(), encoding="utf-8") as f:
            kat = f.read().strip()
        if kat and os.path.isdir(kat):
            return kat
    except OSError:
        pass
    return katalog_domyslny()


def ustaw_katalog_danych(kat):
    """Zapisuje wskazanie. Pusty tekst przywraca katalog domyslny."""
    try:
        if kat:
            os.makedirs(kat, exist_ok=True)
            with open(plik_wskazania(), "w", encoding="utf-8") as f:
                f.write(kat)
        elif os.path.exists(plik_wskazania()):
            os.remove(plik_wskazania())
        return True
    except OSError:
        return False


def sciezka_bazy():
    return os.path.join(katalog_danych(), "baza.json")


def pierwsze_uruchomienie():
    """Czy to nowa instalacja — nie ma ani wskazania, ani lokalnej bazy."""
    return (not os.path.exists(plik_wskazania())
            and not os.path.exists(os.path.join(katalog_domyslny(), "baza.json")))


def szukaj_bazy_w_chmurze():
    """Szuka bazy w katalogach synchronizowanych — OneDrive, Dokumenty, Pulpit.

    Zwraca liste znalezionych plikow, od najswiezszego. Nie wchodzi glebiej
    niz trzy poziomy, zeby nie przeszukiwac calego dysku.
    """
    dom = os.path.expanduser("~")
    korzenie = []
    for wpis in os.listdir(dom) if os.path.isdir(dom) else []:
        pelna = os.path.join(dom, wpis)
        if os.path.isdir(pelna) and wpis.lower().startswith("onedrive"):
            korzenie.append(pelna)
    for nazwa in ("Documents", "Dokumenty", "Desktop", "Pulpit"):
        p = os.path.join(dom, nazwa)
        if os.path.isdir(p):
            korzenie.append(p)

    znalezione = []
    for korzen in korzenie:
        for katalog, podkatalogi, pliki in os.walk(korzen):
            glebokosc = katalog[len(korzen):].count(os.sep)
            if glebokosc >= 3:
                podkatalogi[:] = []
                continue
            # pomijamy katalogi systemowe i tymczasowe
            podkatalogi[:] = [k for k in podkatalogi
                              if not k.startswith((".", "$", "~"))]
            if "baza.json" in pliki:
                sciezka = os.path.join(katalog, "baza.json")
                try:
                    with open(sciezka, encoding="utf-8") as f:
                        dane = json.load(f)
                    if isinstance(dane, dict) and "kierowcy" in dane:
                        znalezione.append({
                            "sciezka": sciezka,
                            "katalog": katalog,
                            "kierowcow": len(dane.get("kierowcy", [])),
                            "wjazdow": len(dane.get("historia", [])),
                            "zmieniony": os.path.getmtime(sciezka),
                        })
                except (OSError, ValueError, json.JSONDecodeError):
                    pass
    znalezione.sort(key=lambda x: -x["zmieniony"])
    return znalezione
SOL = "awf-kierowcy-2026"


def zakoduj_pin(pin):
    return hashlib.sha256((SOL + str(pin)).encode()).hexdigest()


def domyslna_baza():
    return {
        "pin": zakoduj_pin("1234"),
        "motyw": "ciemny",
        "start_pelny": False,
        "admin_haslo": "",
        "admin_email": "",
        "smtp_serwer": "",
        "smtp_port": 587,
        "smtp_login": "",
        "smtp_haslo": "",
        "nazwa": NAZWA,
        "podtytul": PODTYTUL,
        "obiekty": [
            {"id": "zapora", "nazwa": "Zapora słupkowa",
             "miejsce": "Wjazd główny — Marymoncka", "typ": "slupki",
             "sim": "+48 500 100 200", "impuls": 500, "czas": 8,
             "auto": True, "zwloka": 2, "tryb": "prywatny"},
            {"id": "szlaban-g", "nazwa": "Szlaban",
             "miejsce": "Wjazd gospodarczy — Kozielska", "typ": "szlaban",
             "sim": "+48 500 100 201", "impuls": 500, "czas": 10,
             "auto": True, "zwloka": 2, "tryb": "prywatny"},
            {"id": "szlaban-p", "nazwa": "Szlaban",
             "miejsce": "Parking pracowniczy", "typ": "szlaban",
             "sim": "+48 500 100 202", "impuls": 500, "czas": 8,
             "auto": True, "zwloka": 2, "tryb": "prywatny"},
        ],
        "kierowcy": [
            {"imie": "Jan Kowalski", "rola": "Straż Akademicka",
             "tel": "+48 601 234 567", "dni": list(DNI), "od": "00:00",
             "do": "23:59", "wazny": "", "ile": 412, "aktywny": True},
            {"imie": "Anna Nowak", "rola": "Straż Akademicka",
             "tel": "+48 602 345 678", "dni": list(DNI), "od": "00:00",
             "do": "23:59", "wazny": "", "ile": 388, "aktywny": True},
            {"imie": "prof. Barbara Lis", "rola": "Rektorat",
             "tel": "+48 606 111 222", "dni": list(DNI), "od": "05:00",
             "do": "23:00", "wazny": "", "ile": 196, "aktywny": True},
            {"imie": "Trans-Bud sp. z o.o.", "rola": "Dostawca",
             "tel": "+48 603 456 789", "dni": DNI[:5], "od": "06:00",
             "do": "18:00", "wazny": "2026-12-31", "ile": 87, "aktywny": True},
            {"imie": "Cateringowa Kuchnia", "rola": "Dostawca",
             "tel": "+48 662 777 888", "dni": DNI[:5], "od": "05:30",
             "do": "11:00", "wazny": "2027-06-30", "ile": 203, "aktywny": True},
            {"imie": "Robert Wiśniewski", "rola": "Były pracownik",
             "tel": "+48 667 343 434", "dni": list(DNI), "od": "00:00",
             "do": "23:59", "wazny": "", "ile": 0, "aktywny": False},
        ],
        "historia": [],
    }


def wczytaj():
    sciezka = sciezka_bazy()
    if os.path.exists(sciezka):
        try:
            with open(sciezka, encoding="utf-8") as f:
                d = json.load(f)
            wzor = domyslna_baza()
            for k, v in wzor.items():
                d.setdefault(k, v)
            return d
        except (json.JSONDecodeError, OSError):
            pass
    d = domyslna_baza()
    zapisz(d)
    return d


def zapisz(d):
    try:
        sciezka = sciezka_bazy()
        tmp = sciezka + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, sciezka)      # zapis atomowy — brak polowicznych plikow
    except OSError as e:
        print("Nie udalo sie zapisac bazy:", e)


# ==========================================================================
# uprawnienia
# ==========================================================================

# ==========================================================================
# odzyskiwanie dostepu — haslo administratora i kod wysylany na e-mail
# ==========================================================================

SOL_ADMIN = "awf-kierowcy-admin-2026"


def zakoduj_haslo(haslo):
    return hashlib.sha256((SOL_ADMIN + str(haslo)).encode()).hexdigest()


def losowy_kod(dlugosc=6):
    """Kod jednorazowy z generatora kryptograficznego — nie ze zwyklego
    losowania, bo tamto da sie przewidziec."""
    import secrets
    return "".join(secrets.choice("0123456789") for _ in range(dlugosc))


def wyslij_kod(ustawienia, kod, adres):
    """Wysyla kod na wskazany adres. Zwraca (czy_sie_udalo, opis).

    Uzywa konta pocztowego podanego w ustawieniach. Bez niego nie ma
    jak wyslac — program nie ma wlasnego serwera poczty.
    """
    serwer = (ustawienia.get("smtp_serwer") or "").strip()
    login = (ustawienia.get("smtp_login") or "").strip()
    haslo = ustawienia.get("smtp_haslo") or ""
    if not (serwer and login and haslo and adres):
        return False, "Brak ustawień poczty"

    import smtplib
    import ssl
    from email.message import EmailMessage

    wiadomosc = EmailMessage()
    wiadomosc["Subject"] = "AWF KIEROWCY — kod odzyskiwania dostępu"
    wiadomosc["From"] = login
    wiadomosc["To"] = adres
    wiadomosc.set_content(
        "Kod jednorazowy do odblokowania programu AWF KIEROWCY:\n\n"
        f"        {kod}\n\n"
        "Kod jest ważny 15 minut i można go użyć tylko raz.\n\n"
        "Jeśli nie prosiłeś o odblokowanie — ktoś próbuje dostać się\n"
        "do programu na komputerze dyżurki. Sprawdź to.\n")

    port = int(ustawienia.get("smtp_port") or 587)
    try:
        if port == 465:
            with smtplib.SMTP_SSL(serwer, port, timeout=15,
                                  context=ssl.create_default_context()) as p:
                p.login(login, haslo)
                p.send_message(wiadomosc)
        else:
            with smtplib.SMTP(serwer, port, timeout=15) as p:
                p.starttls(context=ssl.create_default_context())
                p.login(login, haslo)
                p.send_message(wiadomosc)
        return True, "Kod wysłany"
    except smtplib.SMTPAuthenticationError:
        return False, "Serwer odrzucił login lub hasło"
    except (smtplib.SMTPException, OSError) as e:
        return False, f"Nie udało się wysłać: {e}"


def sprawdz_dostep(k, teraz=None):
    """Czy kierowca moze teraz wjechac. Zwraca (tak/nie, powod)."""
    teraz = teraz or datetime.now()
    if not k.get("aktywny", True):
        return False, "numer zablokowany"
    if k.get("wazny"):
        try:
            if datetime.strptime(k["wazny"], "%Y-%m-%d").date() < teraz.date():
                return False, "uprawnienie wygasło " + k["wazny"]
        except ValueError:
            pass
    dzien = DNI[teraz.weekday()]
    if dzien not in k.get("dni", DNI):
        return False, "dziś poza harmonogramem"
    g = teraz.strftime("%H:%M")
    od, do = k.get("od", "00:00"), k.get("do", "23:59")
    ok = (od <= g <= do) if od <= do else (g >= od or g <= do)
    return (True, "") if ok else (False, f"poza godzinami {od}–{do}")


def opis_harmonogramu(k):
    dni = k.get("dni", DNI)
    if len(dni) == 7 and k.get("od") == "00:00" and k.get("do") == "23:59":
        return "cały czas"
    if dni == DNI[:5]:
        nazwa = "pn–pt"
    elif len(dni) == 7:
        nazwa = "codziennie"
    else:
        nazwa = ",".join(dni)
    return f"{nazwa} · {k.get('od','00:00')}–{k.get('do','23:59')}"


# ==========================================================================
# scena — zdjecie wjazdu ze slupkami
# ==========================================================================

def cien_styku(szer, wys, krycie):
    """Miekki cien przy podstawie — przyciemnia bruk, nie zakrywa go."""
    szer, wys = max(4, szer), max(4, wys)
    m = 6
    maska = Image.new("L", (szer + m * 2, wys + m * 2), 0)
    d = ImageDraw.Draw(maska)
    for i in range(6, 0, -1):
        t = i / 6.0
        d.ellipse([m + szer * (1 - t) / 2, m + wys * (1 - t) / 2,
                   m + szer - szer * (1 - t) / 2, m + wys - wys * (1 - t) / 2],
                  fill=int(krycie * (1 - t) ** 0.7 + krycie * 0.18))
    maska = maska.filter(ImageFilter.GaussianBlur(max(1.5, szer * 0.06)))
    cien = Image.new("RGBA", maska.size, (12, 14, 16, 0))
    cien.putalpha(maska)
    return cien


class Scena(tk.Canvas):
    """Podglad obiektu. Dla zapory sklada zdjecie, dla szlabanu rysuje."""

    def __init__(self, rodzic, **kw):
        super().__init__(rodzic, highlightthickness=0, bd=0,
                         bg=B["scenaTlo"], **kw)
        self.material = None
        self.typ = "slupki"
        self.nazwa_obiektu = ""
        self.postep = 1.0            # 1 = zamknieta, 0 = otwarta
        self.faza = "spoczynek"
        self.kto = ""
        self.tel = ""
        self.powod = ""
        self.dzis = 0
        self.modul = "LTE · 77%"
        self.zablokowana = False
        self.on_przycisk = None
        # Tryb czysty: scena rysuje samo zdjecie, bez paneli i przyciskow
        # malowanych na plotnie. Stan i polecenia sa osobnymi widgetami
        # obok — na zdjeciu nie da sie ich ulozyc czytelnie.
        self.czysta = False
        self._kiosk = None
        self._cache = {}
        self._trzymaj = []
        self.przyciski = []
        self.bind("<Button-1>", self._klik)

    # ---------------- material zdjeciowy ----------------

    def wczytaj_material(self):
        try:
            uk, tlo = zasob("kiosk-uklad.json"), zasob("kiosk-tlo.jpg")
            if not uk or not tlo:
                return None
            with open(uk, encoding="utf-8") as f:
                dane = json.load(f)
            dane["_tlo"] = Image.open(tlo).convert("RGB")
            for sl in dane["slupki"]:
                kp, pl = zasob(sl["korpus"]), zasob(sl["plyta"])
                if not kp or not pl:
                    return None
                sl["_korpus"] = Image.open(kp).convert("RGBA")
                sl["_plyta"] = Image.open(pl).convert("RGBA")
            return dane
        except (OSError, ValueError, KeyError):
            return None

    # ---------------- uklad ----------------

    def uklad(self, W, H):
        m = 14
        wys_kafli = 74
        szer = (W - 2 * m - 3 * 8) // 4
        przyciski = []
        x = W - m - 4 * szer - 3 * 8
        for _ in range(4):
            przyciski.append((x, H - m - 44, x + szer, H - m - 8))
            x += szer + 8
        return {
            "tytul": (m, m, m + 430, m + 44),
            "kafle": (m, H - m - wys_kafli, W - m, H - m),
            "przyciski": przyciski,
            "wys_kafli": wys_kafli,
        }

    def przelicz(self, W, H):
        """Kadruje zdjecie tak, by zaden slupek nie wszedl pod kafelki."""
        f = self.material
        fw, fh = f["_tlo"].size
        prop = W / float(H)
        LP = self.uklad(W, H)

        wolne = W - 80
        cx_min = min(s["cx"] - s["szer"] * 0.75 for s in f["slupki"])
        cx_max = max(s["cx"] + s["szer"] * 0.75 for s in f["slupki"])
        sk = wolne / float(max(60, cx_max - cx_min))
        kw = int(W / sk)
        kh = int(kw / prop)
        if kw > fw or kh > fh:
            kw = min(fw, int(fh * prop))
            kh = int(kw / prop)
            sk = W / float(kw)
        kx = max(0, min(int(cx_min - 40 / sk), fw - kw))
        gora = min(s["grunt"] - s["wys_korpus"] for s in f["slupki"])
        srodek = sum(s["grunt"] for s in f["slupki"]) / len(f["slupki"])
        ky = max(0, min(int(min(gora - kh * 0.14, srodek - kh * 0.55)), fh - kh))

        kadr = f["_tlo"].crop((kx, ky, kx + kw, ky + kh)).resize(
            (W, H), Image.LANCZOS)

        if B["welon"]:
            welon = Image.new("RGBA", (W, H), (255, 255, 255, B["welon"]))
            kadr = Image.alpha_composite(kadr.convert("RGBA"), welon).convert("RGB")

        naklad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(naklad)
        if self.czysta:
            gotowe = kadr.convert("RGB")
            self._kiosk = {"W": W, "H": H, "sk": sk, "kx": kx, "ky": ky,
                           "uklad": LP, "tk": ImageTk.PhotoImage(gotowe)}
            self._cache = {}
            return
        d.rounded_rectangle(list(LP["tytul"]), radius=11, fill=B["panel"],
                            outline=B["panelRamka"], width=1)
        kx1, ky1, kx2, ky2 = LP["kafle"]
        d.rounded_rectangle([kx1, ky1, kx2, ky2], radius=11, fill=B["panel"],
                            outline=B["panelRamka"], width=1)
        for i, (x1, y1, x2, y2) in enumerate(LP["przyciski"]):
            if i == 0:
                wyp = tuple(int(B["akcent"][j:j + 2], 16)
                            for j in (1, 3, 5)) + (235,)
                ob = None
            else:
                wyp, ob = (255, 255, 255, 34), (255, 255, 255, 96)
            d.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=wyp,
                                outline=ob, width=1)
        gotowe = Image.alpha_composite(kadr.convert("RGBA"), naklad).convert("RGB")

        self._kiosk = {"W": W, "H": H, "sk": sk, "kx": kx, "ky": ky,
                       "uklad": LP, "tk": ImageTk.PhotoImage(gotowe)}
        self._cache = {}

    # ---------------- rysowanie ----------------

    def rysuj(self):
        # Plotno moze zniknac w trakcie przebudowy okna (zmiana motywu).
        # Wtedy po prostu nie rysujemy — nastepne odliczanie trafi juz
        # w nowe plotno.
        try:
            self.delete("all")
        except tk.TclError:
            return
        W = max(self.winfo_width(), 640)
        H = max(self.winfo_height(), 380)
        if self.typ == "slupki" and self.material:
            self._rysuj_zdjecie(W, H)
        else:
            self._rysuj_szlaban(W, H)

    def _rysuj_zdjecie(self, W, H):
        if not self._kiosk or self._kiosk["W"] != W or self._kiosk["H"] != H:
            self.przelicz(W, H)
        k = self._kiosk
        self._trzymaj = [k["tk"]]
        self.create_image(0, 0, image=k["tk"], anchor="nw")

        sk = k["sk"]
        krok = max(0, min(48, int(round(self.postep * 48))))
        for i, sl in enumerate(self.material["slupki"]):
            ex = (sl["cx"] - k["kx"]) * sk
            ey = (sl["grunt"] - k["ky"]) * sk
            szer_e = max(2, int(sl["szer"] * sk))
            udzial = krok / 48.0

            if udzial > 0.02:
                kl = ("cien", i, szer_e, int(udzial * 10))
                if kl not in self._cache:
                    self._cache[kl] = ImageTk.PhotoImage(cien_styku(
                        int(szer_e * (2.1 + 0.9 * udzial)),
                        max(6, int(szer_e * (0.62 + 0.28 * udzial))),
                        int(96 * udzial)))
                self._trzymaj.append(self._cache[kl])
                self.create_image(ex, ey + max(1, int(sl["wys_plyta"] * sk * 0.3)),
                                  image=self._cache[kl], anchor="center")

            kl = ("plyta", i, szer_e)
            if kl not in self._cache:
                hp = max(2, int(sl["wys_plyta"] * sk))
                self._cache[kl] = ImageTk.PhotoImage(
                    sl["_plyta"].resize((szer_e, hp), Image.LANCZOS))
            self._trzymaj.append(self._cache[kl])
            self.create_image(ex, ey, image=self._cache[kl], anchor="s")

            wys_e = max(2, int(sl["wys_korpus"] * sk))
            widoczne = int(wys_e * krok / 48.0)
            if widoczne < 3:
                continue
            kl = ("korpus", i, krok, szer_e)
            if kl not in self._cache:
                pelny = sl["_korpus"].resize((szer_e, wys_e), Image.LANCZOS)
                self._cache[kl] = ImageTk.PhotoImage(
                    pelny.crop((0, 0, szer_e, widoczne)))
            self._trzymaj.append(self._cache[kl])
            dol = ey - max(1, int(sl["wys_plyta"] * sk * 0.45))
            self.create_image(ex, dol - widoczne, image=self._cache[kl], anchor="n")

        self._hud(k["uklad"], W, H)

    def _rysuj_szlaban(self, W, H):
        LP = self.uklad(W, H)
        self._kiosk = {"W": W, "H": H, "uklad": LP}
        gorny = "#1d2f4a" if B is CIEMNY or B["welon"] == 0 else "#cfe3f5"
        self.create_rectangle(0, 0, W, H * 0.62, fill=gorny, outline="")
        self.create_rectangle(0, H * 0.62, W, H, fill="#252a31"
                              if B["welon"] == 0 else "#9ba4ae", outline="")
        for x in range(30, W, 130):
            self.create_rectangle(x, H * 0.80, x + 70, H * 0.80 + 9,
                                  fill="#4a5460" if B["welon"] == 0 else "#eef2f6",
                                  outline="")
        sx, sy = W * 0.30, H * 0.62
        self.create_rectangle(sx - 23, sy - 128, sx + 23, sy, fill="#39424e"
                              if B["welon"] == 0 else "#7b8794", outline="")
        self.create_rectangle(sx - 37, sy - 14, sx + 37, sy, fill="#39424e"
                              if B["welon"] == 0 else "#7b8794", outline="")
        ruch = self.faza not in ("spoczynek", "blokada", "otwarty_staly")
        kol = "#f2b544" if ruch else ("#37c76a" if self.postep < 0.5
                                      else "#d33c40")
        self.create_oval(sx - 13, sy - 154, sx + 13, sy - 128, fill=kol, outline="")

        import math
        kat = math.radians(self.postep * 82 - 82)
        dl = W * 0.56
        x0, y0 = sx, sy - 120
        for i in range(8):
            a, b = i * dl / 8, (i + 1) * dl / 8
            x1, y1 = x0 + a * math.cos(kat), y0 + a * math.sin(kat)
            x2, y2 = x0 + b * math.cos(kat), y0 + b * math.sin(kat)
            self.create_line(x1, y1, x2, y2, width=17,
                             fill="#d33c40" if i % 2 == 0 else "#f0f3f6",
                             capstyle="butt")
        self._hud(LP, W, H)

    def _stan(self):
        """Opis i barwa stanu.

        Czerwony = przejazdu nie ma, zielony = przejazd wolny, zloty = ruch
        albo stan wymagajacy uwagi. Tak samo jak na sygnalizacji drogowej,
        wiec nikt nie musi sie tego uczyc.
        """
        return {
            "spoczynek": (("ZAPORA ZAMKNIĘTA" if self.typ == "slupki"
                           else "SZLABAN OPUSZCZONY"), B["alarm"]),
            "blokada": ("BLOKADA — POŁĄCZENIA IGNOROWANE", B["alarm"]),
            "dzwoni": ("POŁĄCZENIE PRZYCHODZĄCE", B["uwaga"]),
            "otwieranie": (("SŁUPKI OPADAJĄ" if self.typ == "slupki"
                            else "SZLABAN SIĘ PODNOSI"), B["uwaga"]),
            "otwarty": ("PRZEJAZD WOLNY", B["ok"]),
            "otwarty_staly": ("PRZEJAZD OTWARTY NA STAŁE", B["ok"]),
            "zamykanie": (("SŁUPKI PODNOSZĄ SIĘ" if self.typ == "slupki"
                           else "SZLABAN OPADA"), B["uwaga"]),
            "odmowa": ("DOSTĘP ZABLOKOWANY", B["alarm"]),
        }.get(self.faza, ("GOTOWA", B["tekst"]))

    def _hud(self, LP, W, H):
        if self.czysta:
            self.przyciski = []
            return
        x1, y1, x2, y2 = LP["tytul"]
        self.create_text(x1 + 16, (y1 + y2) / 2 - 1,
                         text=self.nazwa_obiektu.upper(), anchor="w",
                         fill=B["naPanelu"], font=("Segoe UI Semibold", 11))
        self.create_text(x2 - 16, (y1 + y2) / 2 - 1,
                         text=datetime.now().strftime("%d.%m.%Y  %H:%M:%S"),
                         anchor="e", fill=B["przygasz"], font=("Consolas", 10))

        opis, kolor = self._stan()
        kx1, ky1, kx2, ky2 = LP["kafle"]
        gy = ky1 + 20
        self.create_text(kx1 + 18, gy, text="STAN", anchor="w",
                         fill=B["przygasz"], font=("Segoe UI", 8))
        self.create_oval(kx1 + 18, gy + 14, kx1 + 27, gy + 23, fill=kolor,
                         outline="")
        self.create_text(kx1 + 34, gy + 19, text=opis, anchor="w", fill=kolor,
                         font=("Segoe UI Semibold", 10))

        px = kx1 + 320
        for etykieta, wartosc in (("WJEŻDŻA", self.kto or "—"),
                                  ("TELEFON", self.powod or self.tel or "—"),
                                  ("MODUŁ", self.modul),
                                  ("DZIŚ", str(self.dzis))):
            if px > LP["przyciski"][0][0] - 110:
                break
            self.create_text(px, gy, text=etykieta, anchor="w",
                             fill=B["przygasz"], font=("Segoe UI", 8))
            self.create_text(px, gy + 19, text=wartosc[:26], anchor="w",
                             fill=B["alarm"] if (etykieta == "TELEFON" and self.powod)
                             else B["naPanelu"], font=("Segoe UI", 10))
            px += 175

        self.przyciski = []
        nazwy = ["Wpuść pojazd", "Otwórz na stałe",
                 "Zamknij" if self.typ == "slupki" else "Opuść",
                 "Zdejmij blokadę" if self.zablokowana else "Blokada"]
        for i, ((bx1, by1, bx2, by2), tekst) in enumerate(
                zip(LP["przyciski"], nazwy)):
            self.create_text((bx1 + bx2) / 2, (by1 + by2) / 2, text=tekst,
                             fill=B["naAkcencie"] if i == 0 else B["naPanelu"],
                             font=("Segoe UI Semibold", 9))
            self.przyciski.append((bx1, by1, bx2, by2, i))

        bw = min(240, (kx2 - kx1) * 0.3)
        self.create_rectangle(kx2 - 18 - bw, ky2 - 12, kx2 - 18, ky2 - 7,
                              fill=B["tlo3"], outline="")
        self.create_rectangle(kx2 - 18 - bw, ky2 - 12,
                              kx2 - 18 - bw + bw * (1 - self.postep), ky2 - 7,
                              fill=B["akcent"], outline="")

    def _klik(self, e):
        for x1, y1, x2, y2, nr in self.przyciski:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                if self.on_przycisk:
                    self.on_przycisk(nr)
                return


# ==========================================================================
# ekran logowania
# ==========================================================================

def okno_pytania(rodzic, tytul, tresc, tak="Tak", nie="Nie", ostrzezenie=False):
    """Pytanie w barwach uczelni zamiast systemowego okienka Windows.

    Systemowe okno wygląda obco: szare tło, inna czcionka, inne przyciski.
    To trzyma się palety programu i wraca True albo False.
    """
    w = tk.Toplevel(rodzic)
    w.title(tytul)
    w.configure(bg=B["tlo2"])
    w.resizable(False, False)
    w.transient(rodzic.winfo_toplevel())
    w.grab_set()
    odpowiedz = {"tak": False}

    tk.Frame(w, bg=B["alarm"] if ostrzezenie else B["akcent"],
             height=4).pack(fill="x")
    r = tk.Frame(w, bg=B["tlo2"], padx=32, pady=26)
    r.pack(fill="both", expand=True)
    tk.Label(r, text=tytul, bg=B["tlo2"], fg=B["tekst"],
             font=("Segoe UI Semibold", 16)).pack(anchor="w")
    tk.Label(r, text=tresc, bg=B["tlo2"], fg=B["tekst2"], justify="left",
             font=("Segoe UI", 11), wraplength=440).pack(anchor="w", pady=(10, 0))

    guziki = tk.Frame(r, bg=B["tlo2"])
    guziki.pack(fill="x", pady=(22, 0))

    def zamknij(wynik):
        odpowiedz["tak"] = wynik
        w.destroy()

    tk.Button(guziki, text=tak, command=lambda: zamknij(True), relief="flat",
              bd=0, cursor="hand2", bg=B["zloto"], fg="#16301f",
              activebackground=B["zloto2"], font=("Segoe UI Semibold", 11),
              padx=24, pady=11).pack(side="right")
    tk.Button(guziki, text=nie, command=lambda: zamknij(False), relief="flat",
              bd=0, cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
              activebackground=B["linia"], font=("Segoe UI", 11),
              padx=22, pady=11).pack(side="right", padx=(0, 10))

    w.bind("<Escape>", lambda _e: zamknij(False))
    w.bind("<Return>", lambda _e: zamknij(True))
    w.update_idletasks()
    g = rodzic.winfo_toplevel()
    x = g.winfo_rootx() + (g.winfo_width() - w.winfo_width()) // 2
    y = g.winfo_rooty() + (g.winfo_height() - w.winfo_height()) // 3
    w.geometry(f"+{max(0, x)}+{max(0, y)}")
    w.wait_window()
    return odpowiedz["tak"]


def okno_tresci(rodzic, tytul, wiersze, szerokosc=520):
    """Okno z trescia w barwach programu — zamiast systemowego komunikatu.

    Wiersze to pary: numer kroku i tekst, albo ("tekst", tresc) dla akapitu,
    ("", "odstep") dla przerwy, ("", "kod:...") dla sciezki do skopiowania.
    """
    w = tk.Toplevel(rodzic)
    w.title(tytul)
    w.configure(bg=B["tlo2"])
    w.resizable(False, False)
    w.transient(rodzic.winfo_toplevel())
    w.grab_set()

    pasek = tk.Frame(w, bg=B["akcent"], height=4)
    pasek.pack(fill="x")

    r = tk.Frame(w, bg=B["tlo2"], padx=30, pady=24)
    r.pack(fill="both", expand=True)

    tk.Label(r, text=tytul, bg=B["tlo2"], fg=B["tekst"],
             font=("Segoe UI Semibold", 15)).pack(anchor="w", pady=(0, 14))

    for lewa, prawa in wiersze:
        if prawa == "odstep":
            tk.Frame(r, bg=B["tlo2"], height=10).pack()
        elif lewa == "tekst" or prawa == "tekst":
            tresc = prawa if lewa == "tekst" else lewa
            tk.Label(r, text=tresc, bg=B["tlo2"], fg=B["tekst2"],
                     font=("Segoe UI", 10), wraplength=szerokosc - 60,
                     justify="left").pack(anchor="w", pady=(0, 4))
        elif str(prawa).startswith("kod:"):
            ramka = tk.Frame(r, bg=B["tlo3"])
            ramka.pack(anchor="w", fill="x", pady=(2, 8), padx=(30, 0))
            tk.Label(ramka, text=prawa[4:], bg=B["tlo3"], fg=B["zloto"],
                     font=("Consolas", 10), padx=12, pady=8).pack(side="left")
        else:
            wiersz = tk.Frame(r, bg=B["tlo2"])
            wiersz.pack(anchor="w", fill="x", pady=2)
            tk.Label(wiersz, text=lewa, bg=B["akcent"], fg=B["naAkcencie"],
                     font=("Segoe UI Semibold", 9), width=3,
                     pady=2).pack(side="left", padx=(0, 12))
            tk.Label(wiersz, text=prawa, bg=B["tlo2"], fg=B["tekst"],
                     font=("Segoe UI", 10), justify="left",
                     wraplength=szerokosc - 110).pack(side="left")

    tk.Button(r, text="Rozumiem", command=w.destroy, relief="flat", bd=0,
              cursor="hand2", bg=B["akcent"], fg=B["naAkcencie"],
              font=("Segoe UI Semibold", 10), padx=22, pady=9
              ).pack(anchor="e", pady=(18, 0))

    w.bind("<Escape>", lambda _e: w.destroy())
    w.bind("<Return>", lambda _e: w.destroy())
    w.update_idletasks()
    g = rodzic.winfo_toplevel()
    x = g.winfo_rootx() + (g.winfo_width() - w.winfo_width()) // 2
    y = g.winfo_rooty() + (g.winfo_height() - w.winfo_height()) // 3
    w.geometry(f"+{max(0, x)}+{max(0, y)}")
    return w


class EkranPin(tk.Frame):
    """Ekran logowania rysowany jako obraz.

    Tkinter nie umie zaokraglonych narozy, cieni ani przejsc tonalnych.
    Karta i klawisze sa wiec rysowane biblioteka obrazow i skladane w jeden
    obrazek, a klikniecie rozpoznajemy po wspolrzednych. Dzieki temu wyglad
    na ekranie jest dokladnie taki, jak na projekcie — co do piksela.

    Barwy: zielen uczelni #036744 jako wypelnienie, zloto #b9975b na klawisz
    zatwierdzenia i obwodki.
    """

    KLAWISZE = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "C", "0", "OK"]

    # Barwy karty osobno dla obu motywow. W ciemnym karta jest zielenia
    # uczelni z bialym napisem, w jasnym — biala z zielonym, bo bialy napis
    # na bieli nie istnieje. Zloto w jasnym motywie jest przyciemnione:
    # #b9975b na bieli ma kontrast 2,8, czyli za malo do czytania.
    MOTYW = {
        "ciemny": dict(
            karta=((6, 120, 80, 246), (2, 72, 48, 250)),
            klaw=((5, 110, 74, 250), (2, 66, 44, 252)),
            ok=((226, 204, 154, 250), (184, 150, 90, 252)),
            napis=(255, 255, 255), napisOk=(16, 44, 31), pod=(216, 235, 226),
            zloto=(232, 214, 176), kropka=(232, 214, 176),
            pusta=(150, 190, 170), c=(255, 150, 150), przyciemnij=84),
        "jasny": dict(
            karta=((255, 255, 255, 242), (236, 244, 240, 246)),
            klaw=((255, 255, 255, 250), (226, 236, 231, 252)),
            ok=((6, 140, 92, 252), (2, 88, 58, 254)),
            napis=(2, 72, 48), napisOk=(255, 255, 255), pod=(74, 110, 92),
            zloto=(138, 110, 52), kropka=(3, 103, 68),
            pusta=(150, 178, 164), c=(179, 38, 38), przyciemnij=52),
    }
    PROM = 22
    KPROM = 16
    MARG = 70          # miejsce na cien dookola karty (przeliczane)

    def __init__(self, rodzic, sprawdz, po_zalogowaniu):
        super().__init__(rodzic, bg=B["tlo"])
        self.sprawdz = sprawdz
        self.po_zalogowaniu = po_zalogowaniu
        # Dwa uklady: karta albo same klawisze na zdjeciu. Bez karty
        # klawisze musza byc wieksze, bo nie maja tla, ktore je zbiera.
        dane = getattr(rodzic, "d", {}) or {}
        self.z_karta = bool(dane.get("karta_logowania", False))
        # Wymiary podstawowe. Program przelicza je przy kazdej zmianie
        # rozmiaru okna, zeby na duzym monitorze klawiatura byla duza,
        # a na malym laptopie miescila sie w calosci.
        self.BAZA = ((440, 700, 118, 68, 13, 276) if self.z_karta
                     else (470, 790, 132, 76, 16, 300))
        self._sr = 1.0
        self._przelicz(1.0)

        # Czy PIN jest wciaz fabryczny — od tego zalezy, czy pokazujemy
        # podpowiedz z numerem 1234.
        self.pin_fabryczny = dane.get("pin") == zakoduj_pin("1234")

        self.wpisany = ""
        self.proby = 0
        self.info = ""
        self.zablokowany = False
        self.blokada_aktualizacji = False
        self.postep_stan = None          # (ulamek, tekst) albo None
        self.pytanie = None              # {"wersja":.., "tak":fn, "nie":fn}
        self._guziki = []
        self.wersja_napis = "v" + wersja_programu()
        self._wcisniety = None
        self._tlo_tk = None
        self._karta_tk = None
        self._rozmiar = None
        self._skala = 1.0

        self.tlo = tk.Label(self, bd=0, bg=B["tlo"], anchor="center")
        self.tlo.place(x=0, y=0, relwidth=1, relheight=1)

        self.plotno = tk.Label(self, bd=0, bg=B["tlo"])
        self.plotno.place(relx=0.5, rely=0.5, anchor="center")
        self.plotno.bind("<ButtonPress-1>", self._wcisnij)
        self.plotno.bind("<ButtonRelease-1>", self._pusc)

        self.rog = tk.Label(self, bd=0, bg=B["tlo2"], fg=B["zloto"],
                            font=("Segoe UI Semibold", 12), padx=14, pady=7,
                            text=self.wersja_napis)
        self.rog.place(relx=0.99, rely=0.98, anchor="se")

        self.bind("<Configure>", self._na_zmiane)
        rodzic.bind("<Configure>", self._na_zmiane, add="+")
        self._pilnuj(0)
        self.bind_all("<Key>", self._klawisz)
        self.after(60, self._na_zmiane)

    # ------------------------------------------------------------------
    # czcionki i ksztalty
    # ------------------------------------------------------------------

    def _przelicz(self, mnoznik):
        """Ustawia wszystkie wymiary na podany mnoznik."""
        self._sr = mnoznik
        kw, kh, klw, klh, od, sy = self.BAZA
        r = lambda v: int(round(v * mnoznik))            # noqa: E731
        self.KW, self.KH = r(kw), r(kh)
        self.KLW, self.KLH, self.ODST = r(klw), r(klh), r(od)
        self.SY = r(sy)
        self.MARG = r(40)

    @staticmethod
    def _czcionka(px, gruby=False):
        """Segoe UI na Windows, DejaVu gdzie indziej."""
        okno = os.environ.get("WINDIR", r"C:\Windows")
        drogi = ([os.path.join(okno, "Fonts", "segoeuib.ttf"),
                  os.path.join(okno, "Fonts", "seguisb.ttf"),
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
                 if gruby else
                 [os.path.join(okno, "Fonts", "segoeui.ttf"),
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        for d in drogi:
            try:
                return ImageFont.truetype(d, px)
            except OSError:
                continue
        return ImageFont.load_default()

    @staticmethod
    def _maska(rozm, prom):
        m = Image.new("L", rozm, 0)
        ImageDraw.Draw(m).rounded_rectangle(
            [0, 0, rozm[0] - 1, rozm[1] - 1], radius=prom, fill=255)
        return m

    @classmethod
    def _przejscie(cls, rozm, gora, dol, prom):
        """Prostokat z pionowym przejsciem tonalnym i zaokraglonymi rogami."""
        pas = Image.new("RGBA", (1, rozm[1]))
        for y in range(rozm[1]):
            t = y / max(1, rozm[1] - 1)
            pas.putpixel((0, y), tuple(
                round(gora[i] + (dol[i] - gora[i]) * t) for i in range(4)))
        out = Image.new("RGBA", rozm, (0, 0, 0, 0))
        out.paste(pas.resize(rozm), (0, 0), cls._maska(rozm, prom))
        return out

    @staticmethod
    def _cien(rozm, prom, rozmycie, moc, odsun):
        im = Image.new("RGBA", (rozm[0] + rozmycie * 4, rozm[1] + rozmycie * 4),
                       (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle(
            [rozmycie * 2, rozmycie * 2 + odsun,
             rozmycie * 2 + rozm[0] - 1, rozmycie * 2 + rozm[1] - 1 + odsun],
            radius=prom, fill=(0, 0, 0, moc))
        return im.filter(ImageFilter.GaussianBlur(rozmycie))

    # ------------------------------------------------------------------
    # tlo
    # ------------------------------------------------------------------

    def _pilnuj(self, ile):
        """Okno maksymalizuje sie w kilku krokach — przez pierwsze trzy
        sekundy pilnujemy, czy tlo nadal pokrywa cala powierzchnie."""
        try:
            if not self.winfo_exists():
                return
            W, H = self.winfo_width(), self.winfo_height()
            brak = (self._tlo_tk is None or self._tlo_tk.width() < W
                    or self._tlo_tk.height() < H)
            if brak and W > 50 and H > 50:
                self._rozmiar = None
                self._na_zmiane()
        except tk.TclError:
            return
        if ile < 12:
            self.after(250, lambda: self._pilnuj(ile + 1))

    @staticmethod
    def _zdjecie_tla():
        obraz = None
        try:
            from tlo_wbudowane import obraz as tlo_z_kodu
            obraz = tlo_z_kodu()
        except ImportError:
            pass
        if obraz is None:
            plik = zasob("logowanie-tlo.jpg")
            if plik:
                try:
                    obraz = Image.open(plik).convert("RGB")
                except (OSError, ValueError):
                    obraz = None
        return obraz

    def _zaslona(self, W, H):
        """Miekka owalna zaslona pod trescia ekranu logowania.

        Rysujemy ja w malej skali i powiekszamy — gradient wychodzi gladki,
        a liczenie idzie szybko. Zasieg dobrany do wysokosci karty, zeby
        zdjecie przy krawedziach ekranu zostalo nietkniete.
        """
        m = 96
        maska = Image.new("L", (m, m), 0)
        px = maska.load()
        for y in range(m):
            for x in range(m):
                dx = (x - m / 2) / (m / 2)
                dy = (y - m / 2) / (m / 2)
                r = (dx * dx + dy * dy) ** 0.5
                if r >= 1:
                    continue
                # 168 w srodku, gasnie do zera przy brzegu owalu
                px[x, y] = int(168 * max(0.0, min(1.0, (1 - r) * 1.55)))
        szer = int(min(W, (self.KW + 2 * self.MARG) * 2.1))
        wys = int(min(H * 1.25, (self.KH + 2 * self.MARG) * 1.35))
        maska = maska.resize((szer, wys), Image.LANCZOS)
        warstwa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ciemne = Image.new("RGBA", (szer, wys), (2, 14, 9, 255))
        warstwa.paste(ciemne, ((W - szer) // 2, (H - wys) // 2), maska)
        return warstwa

    def _na_zmiane(self, _e=None):
        try:
            self.update_idletasks()
            W, H = self.winfo_width(), self.winfo_height()
        except tk.TclError:
            return
        if W < 50 or H < 50 or (W, H) == self._rozmiar:
            return
        self._rozmiar = (W, H)
        # Caly ekran logowania ma zajmowac okolo 86% wysokosci okna.
        # Ograniczenia z dolu i z gory pilnuja, zeby na malym ekranie
        # dalo sie to obsluzyc palcem, a na duzym nie wygladalo jak plakat.
        podstawa = self.BAZA[1] + 2 * 40
        self._przelicz(max(0.55, min(2.2, (H * 0.96) / podstawa)))
        self._skala = 1.0

        obraz = self._zdjecie_tla()
        if obraz is None:
            self.tlo.configure(image="", bg=B["tlo"])
            self.rysuj()
            return
        try:
            sk = max(W / obraz.width, H / obraz.height) * 1.02
            nowy = obraz.resize((max(W, int(obraz.width * sk)),
                                 max(H, int(obraz.height * sk))), Image.LANCZOS)
            lewy = max(0, (nowy.width - W) // 2)
            gorny = max(0, int((nowy.height - H) * 0.45))
            kadr = nowy.crop((lewy, gorny, lewy + W, gorny + H)).convert("RGBA")
            M0 = self.MOTYW["jasny" if B["welon"] else "ciemny"]
            # Przyciemnienie idzie za suwakiem z Ustawien — ekran logowania
            # i panel maja wygladac tak samo.
            rodzic = self.master
            proc = 46
            try:
                proc = int((getattr(rodzic, "d", {}) or {}).get(
                    "przezroczystosc_tla", 46))
            except (TypeError, ValueError):
                pass
            proc = max(0, min(100, proc))
            kadr = Image.alpha_composite(
                kadr, Image.new("RGBA", (W, H),
                                (4, 14, 9, int(proc * 255 / 100 * 0.62))))
            # ...a ciemne podloze dajemy tylko tam, gdzie leza napisy.
            # Pomiar: pod trescia jasnosc spada ze 100 na 37, wiec kontrast
            # opisow rosnie z 4,6 do 11,3, a zdjecie dookola zostaje jasne.
            kadr.alpha_composite(self._zaslona(W, H))
            win = Image.new("L", (W, H), 0)
            ImageDraw.Draw(win).ellipse(
                [-W * 0.28, -H * 0.38, W * 1.28, H * 1.38], fill=255)
            win = win.filter(ImageFilter.GaussianBlur(
                max(40, min(W, H) // 6))).point(lambda v: int((255 - v) * 0.30))
            kadr.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (0, 0), win)
            self._tlo_pil = kadr
            self._tlo_tk = ImageTk.PhotoImage(kadr.convert("RGB"))
            self.tlo.configure(image=self._tlo_tk)
        except (OSError, ValueError, MemoryError):
            self.tlo.configure(image="", bg=B["tlo"])
        self.rysuj()

    # ------------------------------------------------------------------
    # rysowanie karty
    # ------------------------------------------------------------------

    def _prostokaty(self):
        """Polozenie klawiszy w ukladzie karty, przed przeskalowaniem."""
        szer = 3 * self.KLW + 2 * self.ODST
        sx = (self.KW - szer) // 2
        out = []
        for i, znak in enumerate(self.KLAWISZE):
            out.append((sx + (i % 3) * (self.KLW + self.ODST),
                        self.SY + (i // 3) * (self.KLH + self.ODST),
                        self.KLW, self.KLH, znak))
        return out

    def rysuj(self, _e=None):
        """Rysuje caly ekran w rozmiarze policzonym od wysokosci okna.

        Nic nie jest tu zmniejszane po fakcie — kazdy odstep, czcionka
        i promien narozy powstaje juz w docelowej wielkosci. Dzieki temu
        na monitorze 1920x1080 klawiatura jest duza i ostra, a na malym
        laptopie miesci sie w calosci.
        """
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        k = self._sr                      # mnoznik wielkosci
        def p(v):                         # skrot: wartosc w pikselach ekranu
            return int(round(v * k))

        M0 = self.MOTYW["jasny" if B["welon"] else "ciemny"]
        if not self.z_karta:
            M0 = dict(self.MOTYW["ciemny"], przyciemnij=M0["przyciemnij"])
        KW, KH, R = self.KW, self.KH, p(self.PROM)
        M = self.MARG

        plotno = Image.new("RGBA", (KW + 2 * M, KH + 2 * M), (0, 0, 0, 0))
        karta = Image.new("RGBA", (KW, KH), (0, 0, 0, 0))
        if self.z_karta:
            plotno.alpha_composite(
                self._cien((KW, KH), R, p(30), 100, p(20)),
                (M - p(60), M - p(60)))
            plotno.alpha_composite(
                self._cien((KW, KH), R, p(10), 130, p(6)),
                (M - p(20), M - p(20)))
            karta.alpha_composite(self._przejscie((KW, KH), *M0["karta"], R))
        d = ImageDraw.Draw(karta)
        if self.z_karta:
            d.rounded_rectangle([0, 0, KW - 1, KH - 1], radius=R,
                                outline=M0["zloto"] + (190,), width=1)
            d.line([R + p(8), 1, KW - R - p(8), 1],
                   fill=(255, 255, 255, 60), width=1)

        # --- godlo ---
        gr = p(100 if self.z_karta else 116)
        gy = p(40)
        # Godlo nie ma juz bialego kola — poswiata daje mu oddech na zdjeciu
        # i odkleja je od tla, zeby nie wtapialo sie w budynek.
        pos = Image.new("RGBA", (int(gr * 1.7),) * 2, (0, 0, 0, 0))
        ImageDraw.Draw(pos).ellipse(
            [gr * 0.22, gr * 0.22, gr * 1.48, gr * 1.48],
            fill=(0, 0, 0, 96) if not B["welon"] else (255, 255, 255, 120))
        karta.alpha_composite(pos.filter(ImageFilter.GaussianBlur(p(17))),
                              ((KW - pos.width) // 2, gy - int(gr * 0.35)))
        godlo = None
        try:
            from tlo_wbudowane import godlo as godlo_z_kodu
            godlo = godlo_z_kodu()
        except ImportError:
            pass
        if godlo is None:
            plik = zasob("godlo-kolo.png") or zasob("godlo-awf.png")
            if plik:
                try:
                    godlo = Image.open(plik).convert("RGBA")
                except (OSError, ValueError):
                    godlo = None
        if godlo is not None:
            karta.alpha_composite(godlo.resize((gr, gr), Image.LANCZOS),
                                  ((KW - gr) // 2, gy))
        pier = int(gr * 1.16)
        d.ellipse([(KW - pier) // 2, gy - int(gr * 0.08),
                   (KW + pier) // 2, gy - int(gr * 0.08) + pier],
                  outline=M0["zloto"] + (130,), width=max(1, p(1)))

        # --- nazwa i podtytul ---
        ty = gy + gr + p(42)
        cz_nazwa = self._czcionka(p(27 if self.z_karta else 31), True)
        d.text((KW / 2 + p(1), ty + p(1)), NAZWA, font=cz_nazwa,
               fill=(0, 0, 0, 130), anchor="mm")
        d.text((KW / 2, ty), NAZWA, font=cz_nazwa, fill=M0["zloto"],
               anchor="mm")
        d.line([KW / 2 - p(50), ty + p(22), KW / 2 + p(50), ty + p(22)],
               fill=M0["zloto"] + (190,), width=max(1, p(1)))
        cz_pod = self._czcionka(p(18))
        d.text((KW / 2 + p(1), ty + p(41)), PODTYTUL, font=cz_pod,
               fill=(0, 0, 0, 110), anchor="mm")
        d.text((KW / 2, ty + p(40)), PODTYTUL, font=cz_pod, fill=M0["pod"],
               anchor="mm")

        # --- kropki PIN-u ---
        # Wielkosc liczona od klawisza, nie stala: kropka ma 15% szerokosci
        # klawisza, odstep 40%. Przy wiekszej klawiaturze rosna razem z nia,
        # wiec z drugiego konca dyzurki widac, ile cyfr juz wpisano.
        ky = ty + p(56)
        prom = max(p(6), int(self.KLW * 0.15) // 2)
        odstep = max(p(22), int(self.KLW * 0.40))
        ile = max(4, len(self.wpisany))
        x0 = KW / 2 - (ile - 1) * odstep / 2
        for i in range(ile):
            x = x0 + i * odstep
            pole = [x - prom, ky, x + prom, ky + 2 * prom]
            if i < len(self.wpisany):
                d.ellipse(pole, fill=M0["kropka"])
                # jasna obwodka odkleja wypelniona kropke od tla
                d.ellipse(pole, outline=(255, 255, 255, 90),
                          width=max(1, p(1)))
            else:
                d.ellipse(pole, outline=M0["pusta"], width=max(2, p(3)))
        if self.info:
            d.text((KW / 2, ky + 2 * prom + p(18)), self.info,
                   font=self._czcionka(p(15), True), fill=(255, 150, 150),
                   anchor="mm")

        # --- klawiatura ---
        blok = (self.zablokowany or self.blokada_aktualizacji
                or self.pytanie is not None)
        KPR = p(self.KPROM)
        for x, y, kw, kh, znak in self._prostokaty():
            wcisniety = self._wcisniety == znak
            karta.alpha_composite(
                self._cien((kw, kh), KPR, p(6), 60 if wcisniety else 120, p(3)),
                (x - p(12), y - p(12)))
            if znak == "OK":
                gora, dol = M0["ok"]
                barwa = M0["napisOk"]
                fnt = self._czcionka(p(21 if self.z_karta else 23), True)
            else:
                gora, dol = M0["klaw"]
                fnt = self._czcionka(p(25 if self.z_karta else 27), True)
                barwa = M0["c"] if znak == "C" else M0["napis"]
            if wcisniety:
                gora, dol = dol, gora
            kl = self._przejscie((kw, kh), gora, dol, KPR)
            if blok:
                kl = Image.blend(kl, Image.new("RGBA", (kw, kh), (0, 0, 0, 190)),
                                 0.45)
                barwa = tuple(int(c * 0.55) + 40 for c in barwa)
            dl = ImageDraw.Draw(kl)
            dl.rounded_rectangle([0, 0, kw - 1, kh - 1], radius=KPR,
                                 outline=M0["zloto"] + (90,), width=1)
            if not wcisniety:
                dl.line([KPR, 1, kw - KPR, 1], fill=(255, 255, 255, 70), width=1)
                dl.arc([2, 2, kw - 3, kh // 2], 190, 350,
                       fill=(255, 255, 255, 26), width=1)
            dl.line([KPR, kh - 2, kw - KPR, kh - 2], fill=(0, 0, 0, 110), width=1)
            dl.text((kw / 2, kh / 2 + p(1)), znak, font=fnt,
                    fill=(0, 0, 0, 110), anchor="mm")
            dl.text((kw / 2, kh / 2), znak, font=fnt, fill=barwa, anchor="mm")
            karta.alpha_composite(kl, (x, y))

        szer = 3 * self.KLW + 2 * self.ODST
        sx = (KW - szer) // 2

        # --- pytanie o aktualizacje zamiast klawiatury ---
        self._guziki = []
        if self.pytanie is not None:
            wys = 4 * (self.KLH + self.ODST)
            zaslona = self._przejscie((szer + p(24), wys), (0, 0, 0, 170),
                                      (0, 0, 0, 200), p(16))
            karta.alpha_composite(zaslona, (sx - p(12), self.SY - p(6)))
            gy2 = self.SY + p(30)
            d.text((KW / 2, gy2 + p(6)), "Dostępna nowa wersja",
                   font=self._czcionka(p(18), True), fill=M0["zloto"],
                   anchor="mm")
            d.text((KW / 2, gy2 + p(38)), self.pytanie["wersja"],
                   font=self._czcionka(p(30), True), fill=(255, 255, 255),
                   anchor="mm")
            d.text((KW / 2, gy2 + p(72)), "Wgrać teraz? Potrwa chwilę,",
                   font=self._czcionka(p(15)), fill=(215, 232, 222), anchor="mm")
            d.text((KW / 2, gy2 + p(94)), "program zamknie się i wróci sam.",
                   font=self._czcionka(p(15)), fill=(215, 232, 222), anchor="mm")
            for i, (napis, klucz) in enumerate((("Wgraj teraz", "tak"),
                                                ("Nie teraz", "nie"))):
                gw, gh = szer - p(40), p(52)
                gx = sx + p(20)
                gyy = gy2 + p(112) + i * (gh + p(12))
                glowny = klucz == "tak"
                grf = self._przejscie(
                    (gw, gh), *(M0["ok"] if glowny else M0["klaw"]), p(14))
                dg = ImageDraw.Draw(grf)
                dg.rounded_rectangle([0, 0, gw - 1, gh - 1], radius=p(14),
                                     outline=M0["zloto"] + (110,), width=1)
                dg.text((gw / 2, gh / 2), napis,
                        font=self._czcionka(p(18), True),
                        fill=M0["napisOk"] if glowny else M0["napis"],
                        anchor="mm")
                karta.alpha_composite(grf, (gx, gyy))
                self._guziki.append((gx, gyy, gw, gh, klucz))

        # --- pasek postepu albo napis o PIN-ie fabrycznym ---
        py = self.SY + 4 * (self.KLH + self.ODST) + p(8)
        if self.postep_stan is not None:
            ulamek, opis = self.postep_stan
            d.text((sx, py), opis, font=self._czcionka(p(15), True),
                   fill=M0["zloto"])
            d.text((sx + szer, py), f"{round(ulamek * 100)}%",
                   font=self._czcionka(p(15), True), fill=M0["pod"], anchor="ra")
            d.rounded_rectangle([sx, py + p(22), sx + szer, py + p(29)],
                                radius=p(4), fill=(0, 0, 0, 120))
            if ulamek > 0:
                d.rounded_rectangle(
                    [sx, py + p(22), sx + max(p(8), int(szer * ulamek)),
                     py + p(29)], radius=p(4), fill=M0["zloto"])
        elif self.pin_fabryczny:
            # Podpowiedz znika, gdy tylko ktos ustawi wlasny PIN — inaczej
            # wisialaby na ekranie na stale i podawala numer, ktory juz
            # nie dziala.
            cz_st = self._czcionka(p(15))
            napis = "PIN fabryczny 1234 — zmień po pierwszym logowaniu"
            if not self.z_karta:
                d.text((KW / 2 + p(1), py + p(5)), napis,
                       font=cz_st, fill=(0, 0, 0, 120), anchor="mm")
            d.text((KW / 2, py + p(4)), napis,
                   font=cz_st, fill=M0["pod"], anchor="mm")

        d.text((KW / 2, py + p(62)), "Nie pamiętam PIN-u",
               font=self._czcionka(p(16)), fill=M0["zloto"], anchor="mm")
        d.line([KW / 2 - p(82), py + p(76), KW / 2 + p(82), py + p(76)],
               fill=M0["zloto"] + (160,), width=max(1, p(1)))
        self._odnosnik = (KW / 2 - p(90), py + p(48), p(180), p(36))

        plotno.alpha_composite(karta, (M, M))
        karta = plotno

        # sklejamy z tlem — tkinter nie znosi przezroczystosci w Label
        if self._tlo_tk is not None and getattr(self, "_tlo_pil", None):
            W, H = self._rozmiar
            lx = max(0, (W - karta.width) // 2)
            ly = max(0, (H - karta.height) // 2)
            podklad = self._tlo_pil.crop(
                (lx, ly, lx + karta.width, ly + karta.height))
        else:
            podklad = Image.new("RGBA", karta.size,
                                tuple(int(B["tlo"][i:i + 2], 16)
                                      for i in (1, 3, 5)) + (255,))
        gotowe = Image.alpha_composite(podklad.convert("RGBA"), karta)
        self._karta_tk = ImageTk.PhotoImage(gotowe.convert("RGB"))
        self.plotno.configure(image=self._karta_tk)

    # ------------------------------------------------------------------
    # obsluga
    # ------------------------------------------------------------------

    def _z_ekranu(self, e):
        """Wspolrzedne klikniecia w ukladzie karty.

        Obrazek jest wiekszy od karty o margines na cien, a przy malym
        ekranie jeszcze przeskalowany — jedno i drugie trzeba odjac.
        """
        return e.x - self.MARG, e.y - self.MARG

    def _wcisnij(self, e):
        if self.pytanie is not None:
            return
        if self.zablokowany or self.blokada_aktualizacji:
            return
        x, y = self._z_ekranu(e)
        for kx, ky, kw, kh, znak in self._prostokaty():
            if kx <= x <= kx + kw and ky <= y <= ky + kh:
                self._wcisniety = znak
                self.rysuj()
                return

    def _pusc(self, e):
        znak = self._wcisniety
        self._wcisniety = None
        x, y = self._z_ekranu(e)
        if self.pytanie is not None:
            for gx, gy, gw, gh, klucz in self._guziki:
                if gx <= x <= gx + gw and gy <= y <= gy + gh:
                    odpowiedz = self.pytanie.get(klucz)
                    self.pytanie = None
                    self.rysuj()
                    if callable(odpowiedz):
                        odpowiedz()
                    return
            return
        ox, oy, ow, oh = getattr(self, "_odnosnik", (0, 0, 0, 0))
        if ox <= x <= ox + ow and oy <= y <= oy + oh:
            self.rysuj()
            self._zapomnialem()
            return
        if znak is None:
            return
        for kx, ky, kw, kh, z in self._prostokaty():
            if z == znak and kx <= x <= kx + kw and ky <= y <= ky + kh:
                self.klik(znak)
                return
        self.rysuj()

    def klik(self, znak):
        # Pytanie o aktualizacje zaslania klawiature — takze ta fizyczna,
        # inaczej dalo by sie wpisac PIN "na slepo" pod zaslona.
        if (self.zablokowany or self.blokada_aktualizacji
                or self.pytanie is not None):
            return
        if znak == "C":
            self.wpisany = ""
        elif znak == "OK":
            self._sprawdz()
            return
        elif len(self.wpisany) < 8:
            self.wpisany += znak
        self.info = ""
        self.rysuj()

    def _klawisz(self, e):
        if not self.winfo_ismapped():
            return
        if e.char.isdigit():
            self.klik(e.char)
        elif e.keysym == "Return":
            self.klik("OK")
        elif e.keysym == "BackSpace":
            self.klik("C")

    def _sprawdz(self):
        if self.sprawdz(self.wpisany):
            self.unbind_all("<Key>")
            self.po_zalogowaniu()
        else:
            self.proby += 1
            self.wpisany = ""
            if self.proby >= 5:
                self.zablokowany = True
                self.info = "Zablokowano — uruchom ponownie"
            else:
                self.info = f"Błędny PIN — próba {self.proby} z 5"
            self.rysuj()

    # ------------------------------------------------------------------
    # aktualizacja
    # ------------------------------------------------------------------

    def zapytaj_o_aktualizacje(self, wersja, tak, nie):
        """Pyta raz. Odpowiedz zapamietuje program, nie ten ekran."""
        self.pytanie = {"wersja": wersja, "tak": tak, "nie": nie}
        self.info = ""
        self.rysuj()

    def komunikat(self, tekst, kolor=None):
        """Napis w rogu ekranu — wersja albo stan sprawdzania."""
        try:
            self.rog.configure(text=tekst, fg=kolor or B["zloto"])
        except tk.TclError:
            pass

    def postep(self, ulamek, tekst=""):
        """Pasek wgrywania aktualizacji. Klawiatura jest wtedy zablokowana —
        podmiana plikow w trakcie logowania skonczylaby sie zamknieciem
        programu komus pod reka."""
        self.postep_stan = (max(0.0, min(1.0, float(ulamek))), tekst)
        self.blokada_aktualizacji = True
        self.info = "Trwa aktualizacja — poczekaj"
        self.rysuj()

    def schowaj_postep(self):
        self.postep_stan = None
        self.blokada_aktualizacji = False
        self.info = ""
        self.rysuj()

    def _zapomnialem(self):
        """Odzyskanie dostepu: haslem administratora albo kodem z poczty."""
        d = self.master.d if hasattr(self.master, "d") else wczytaj()

        if not d.get("admin_haslo") and not d.get("admin_email"):
            okno_tresci(
                self, "Odzyskiwanie dostępu nie jest ustawione",
                [("Nikt nie ustawił hasła administratora ani adresu e-mail, "
                  "więc program nie ma jak potwierdzić, kto prosi o dostęp.",
                  "tekst"),
                 ("", "odstep"),
                 ("Zaloguj się PIN-em i wejdź w Ustawienia → "
                  "Odzyskiwanie dostępu, żeby to ustawić.", "tekst"),
                 ("", "odstep"),
                 ("Jeśli nikt nie zna PIN-u, dostęp do pliku z bazą ma tylko "
                  "administrator komputera — proszę zwrócić się do działu "
                  "informatycznego.", "tekst")])
            return

        w = tk.Toplevel(self)
        w.title("Odzyskiwanie dostępu")
        w.configure(bg=B["tlo2"])
        w.resizable(False, False)
        w.transient(self.winfo_toplevel())
        w.grab_set()
        tk.Frame(w, bg=B["akcent"], height=4).pack(fill="x")
        r = tk.Frame(w, bg=B["tlo2"], padx=30, pady=24)
        r.pack(fill="both", expand=True)

        tk.Label(r, text="Odzyskiwanie dostępu", bg=B["tlo2"], fg=B["tekst"],
                 font=("Segoe UI Semibold", 15)).pack(anchor="w")
        tk.Label(r, text="Dostęp może przywrócić tylko administrator.",
                 bg=B["tlo2"], fg=B["przygasz"],
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 16))

        stan = {"kod": None, "czas": None}

        def etykieta(t):
            tk.Label(r, text=t, bg=B["tlo2"], fg=B["przygasz"],
                     font=("Segoe UI", 9), anchor="w").pack(anchor="w",
                                                            pady=(10, 3))

        def pole(ukryj=False):
            e = tk.Entry(r, bg=B["tlo3"], fg=B["tekst"], relief="flat",
                         font=("Segoe UI", 12), insertbackground=B["tekst"],
                         show="●" if ukryj else "")
            e.pack(fill="x", ipady=7)
            return e

        komunikat = tk.Label(r, text="", bg=B["tlo2"], fg=B["alarm"],
                             font=("Segoe UI", 9), wraplength=420,
                             justify="left")

        # --- droga 1: haslo administratora ---
        if d.get("admin_haslo"):
            etykieta("Hasło administratora")
            p_haslo = pole(ukryj=True)
        else:
            p_haslo = None

        # --- droga 2: kod na e-mail ---
        p_kod = None
        if d.get("admin_email"):
            adres = d["admin_email"]
            zamaskowany = adres
            if "@" in adres:
                nazwa, reszta = adres.split("@", 1)
                zamaskowany = (nazwa[:2] + "•" * max(1, len(nazwa) - 2)
                               + "@" + reszta)
            etykieta(f"Kod wysłany na {zamaskowany}")
            ramka = tk.Frame(r, bg=B["tlo2"])
            ramka.pack(fill="x")
            p_kod = tk.Entry(ramka, bg=B["tlo3"], fg=B["tekst"], relief="flat",
                             font=("Consolas", 14), insertbackground=B["tekst"],
                             width=10)
            p_kod.pack(side="left", ipady=7)

            def wyslij():
                stan["kod"] = losowy_kod()
                stan["czas"] = datetime.now()
                udalo, opis = wyslij_kod(d, stan["kod"], adres)
                komunikat.configure(
                    text=("Kod wysłany. Sprawdź skrzynkę — ważny 15 minut."
                          if udalo else opis),
                    fg=B["ok"] if udalo else B["alarm"])
                if not udalo:
                    stan["kod"] = None

            tk.Button(ramka, text="Wyślij kod", command=wyslij, relief="flat",
                      bd=0, cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                      font=("Segoe UI", 10), padx=16, pady=8
                      ).pack(side="left", padx=(8, 0))

        etykieta("Nowy PIN (4–8 cyfr)")
        p_nowy = pole(ukryj=True)
        komunikat.pack(anchor="w", pady=(12, 0))

        def zatwierdz():
            nowy = p_nowy.get().strip()
            if not nowy.isdigit() or not 4 <= len(nowy) <= 8:
                komunikat.configure(text="PIN musi mieć od 4 do 8 cyfr.",
                                    fg=B["alarm"])
                return

            uprawniony = False
            if p_haslo is not None and p_haslo.get():
                if zakoduj_haslo(p_haslo.get()) == d.get("admin_haslo"):
                    uprawniony = True
                else:
                    komunikat.configure(text="Błędne hasło administratora.",
                                        fg=B["alarm"])
                    return
            elif p_kod is not None and p_kod.get().strip():
                if not stan["kod"]:
                    komunikat.configure(text="Najpierw wyślij kod.",
                                        fg=B["alarm"])
                    return
                minelo = (datetime.now() - stan["czas"]).total_seconds()
                if minelo > 900:
                    stan["kod"] = None
                    komunikat.configure(text="Kod stracił ważność. Wyślij nowy.",
                                        fg=B["alarm"])
                    return
                if p_kod.get().strip() == stan["kod"]:
                    uprawniony = True
                    stan["kod"] = None          # kod jednorazowy
                else:
                    komunikat.configure(text="Błędny kod.", fg=B["alarm"])
                    return
            else:
                komunikat.configure(
                    text="Podaj hasło administratora albo kod z poczty.",
                    fg=B["alarm"])
                return

            if uprawniony:
                d["pin"] = zakoduj_pin(nowy)
                zapisz(d)
                w.destroy()
                self.proby = 0
                self.zablokowany = False
                self.wpisany = ""
                self.info = ""
                self.rysuj()
                okno_tresci(self, "PIN zmieniony",
                            [("Nowy PIN działa od razu. Zaloguj się nim.",
                              "tekst")])

        guziki = tk.Frame(r, bg=B["tlo2"])
        guziki.pack(fill="x", pady=(18, 0))
        tk.Button(guziki, text="Ustaw nowy PIN", command=zatwierdz,
                  relief="flat", bd=0, cursor="hand2", bg=B["akcent"],
                  fg=B["naAkcencie"], font=("Segoe UI Semibold", 10),
                  padx=20, pady=9).pack(side="right")
        tk.Button(guziki, text="Anuluj", command=w.destroy, relief="flat",
                  bd=0, cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                  font=("Segoe UI", 10), padx=18, pady=9
                  ).pack(side="right", padx=(0, 8))

        w.bind("<Escape>", lambda _e: w.destroy())
        w.update_idletasks()
        g = self.winfo_toplevel()
        x = g.winfo_rootx() + (g.winfo_width() - w.winfo_width()) // 2
        y = g.winfo_rooty() + 70
        w.geometry(f"+{max(0, x)}+{max(0, y)}")

# ==========================================================================
# okno glowne
# ==========================================================================

class App(tk.Tk):
    ZAKLADKI = [("podglad", "PODGLĄD"), ("kierowcy", "KIEROWCY"),
                ("sterownik", "STEROWNIK"), ("historia", "HISTORIA"),
                ("ustawienia", "USTAWIENIA")]

    def __init__(self):
        super().__init__()
        self._nowa_instalacja = pierwsze_uruchomienie()
        self.d = wczytaj()
        zastosuj_motyw(self.d.get("motyw") == "jasny",
                       self.d.get("styl"))
        self.obiekt = min(obiekt_z_polecenia(), len(self.d["obiekty"]) - 1)
        self.wybrany = 0
        self.animacja = None
        self.stany = {o["id"]: {"postep": 1.0, "faza": "spoczynek",
                                "blokada": False}
                      for o in self.d["obiekty"]}

        self.title(f"{self.d.get('nazwa', NAZWA)} — {self.d.get('podtytul', PODTYTUL)}")
        self.geometry("1360x860")
        self.minsize(min(980, self.winfo_screenwidth() - 40),
                     min(620, self.winfo_screenheight() - 80))
        self.otworz_na_caly_ekran()
        self.after(300, self._dopilnuj_maksymalizacji)
        self.after(900, self._dopilnuj_maksymalizacji)
        # W dyzurce monitor stoi caly czas, wiec program otwiera sie
        # od razu na pelnym ekranie. Wyjscie klawiszem Escape albo F11.
        if self.d.get("start_pelny", False):
            self.after(120, self._wlacz_pelny_start)
        self.configure(bg=B["tlo"])
        ik = zasob("ikona.ico")
        if ik and sys.platform == "win32":
            try:
                self.iconbitmap(ik)
            except tk.TclError:
                pass

        self.ekran_pin = EkranPin(self, self._pin_ok, self._zalogowano)
        self.ekran_pin.pack(fill="both", expand=True)

        # Aktualizacji nie sprawdzamy przed PIN-em — ekran logowania ma byc
        # ekranem logowania. Pytanie wyskakuje po zalogowaniu, gdy dyzurny
        # widzi juz panel i moze swiadomie zdecydowac.
        self._zalogowany = False
        self._akt_stan = None

        # Program w dyzurce nie moze zniknac przez przypadkowe klikniecie
        # krzyzyka albo Alt+F4 — pytamy o potwierdzenie.
        self._zamykam_sam = False
        self.protocol("WM_DELETE_WINDOW", self.zamknij_program)

        self.bind("<Escape>", self._escape_obiekt, add="+")
        self.bind("<F11>", lambda _e: self.pelny_ekran())
        self.bind("<Escape>", self._escape)

    def zamknij_program(self):
        """Pyta, zanim zamknie. Aktualizacja zamyka program po swojemu
        i wtedy nie pytamy — ustawia znacznik przed wywolaniem destroy."""
        if self._zamykam_sam:
            self.destroy()
            return
        if okno_pytania(
                self, "Zamknąć program?",
                "Zapora i szlabany przestaną być obsługiwane z tego "
                "komputera do czasu ponownego uruchomienia.",
                tak="Zamknij program", nie="Zostaw otwarty",
                ostrzezenie=True):
            self._zamykam_sam = True
            self.destroy()

    def _escape_obiekt(self, _e=None):
        if getattr(self, "obiekt_otwarty", False):
            self.zamknij_obiekt()
            return "break"
        return None

    def _escape(self, _e=None):
        """Escape wychodzi z pelnego ekranu, ale nie zamyka programu."""
        if getattr(self, "_pelny", False):
            self.pelny_ekran()

    def _wlacz_pelny_start(self):
        try:
            self.attributes("-fullscreen", True)
            self._pelny = True
            self.d["pelny_ekran"] = True
        except tk.TclError:
            pass

    def otworz_na_caly_ekran(self):
        """Program otwiera sie zmaksymalizowany. W dyzurce monitor stoi caly
        czas, wiec nie ma sensu zaczynac od malego okna.

        Sprawdzamy, czy maksymalizacja zadzialala. Niektore srodowiska
        przyjmuja polecenie i nic nie robia — wtedy ustawiamy rozmiar recznie.
        """
        self.update_idletasks()
        for proba in ("zoomed", "-zoomed", "recznie"):
            try:
                if proba == "zoomed":
                    self.state("zoomed")
                elif proba == "-zoomed":
                    self.attributes("-zoomed", True)
                else:
                    w = self.winfo_screenwidth()
                    h = self.winfo_screenheight() - 60
                    self.geometry(f"{w}x{h}+0+0")
            except tk.TclError:
                continue
            self.update_idletasks()
            # sprawdzamy obie strony — samo dopasowanie szerokosci nie wystarcza,
            # okno moze byc wtedy wyzsze niz monitor
            if (self.winfo_width() >= self.winfo_screenwidth() * 0.92
                    and self.winfo_height() <= self.winfo_screenheight()):
                return
        # ostatnia deska ratunku
        self.geometry(f"{self.winfo_screenwidth()}x"
                      f"{self.winfo_screenheight() - 60}+0+0")

    def _dopilnuj_maksymalizacji(self):
        """Niektore okiennice maksymalizuja dopiero po pokazaniu okna.
        Sprawdzamy jeszcze raz po chwili i poprawiamy, gdy trzeba."""
        try:
            if getattr(self, "_pelny", False):
                return
            za_waskie = self.winfo_width() < self.winfo_screenwidth() * 0.92
            za_wysokie = self.winfo_height() > self.winfo_screenheight()
            if za_waskie or za_wysokie:
                self.otworz_na_caly_ekran()
        except tk.TclError:
            pass

    # ---------------- logowanie ----------------

    def _pin_ok(self, pin):
        return zakoduj_pin(pin) == self.d.get("pin")

    def _pierwsze_uruchomienie(self):
        """Nowa instalacja — pytamy, skad wziac dane, zamiast kazac
        wpisywac wszystko od nowa."""
        znalezione = szukaj_bazy_w_chmurze()

        w = tk.Toplevel(self)
        w.title("Pierwsze uruchomienie")
        w.configure(bg=B["tlo2"])
        w.resizable(False, False)
        w.transient(self)
        w.grab_set()
        r = tk.Frame(w, bg=B["tlo2"], padx=30, pady=26)
        r.pack()

        tk.Label(r, text="Skąd wziąć dane?", bg=B["tlo2"], fg=B["tekst"],
                 font=("Segoe UI Semibold", 15)).pack(anchor="w")
        tk.Label(r, text="To pierwsze uruchomienie na tym komputerze.",
                 bg=B["tlo2"], fg=B["przygasz"],
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 18))

        def zamknij_i_odswiez():
            self.d = wczytaj()
            try:
                self.odswiez_kierowcow()
                self.odswiez_historie()
                self.lbl_katalog.configure(text=katalog_danych())
            except (AttributeError, tk.TclError):
                pass
            w.destroy()

        def uzyj(wpis):
            ustaw_katalog_danych(wpis["katalog"])
            self.log("baza z: " + wpis["katalog"])
            zamknij_i_odswiez()

        if znalezione:
            tk.Label(r, text="ZNALEZIONE BAZY", bg=B["tlo2"], fg=B["zloto"],
                     font=("Segoe UI Semibold", 8)).pack(anchor="w",
                                                         pady=(0, 6))
            for wpis in znalezione[:4]:
                karta = tk.Frame(r, bg=B["tlo3"], padx=14, pady=11)
                karta.pack(fill="x", pady=(0, 7))
                opis = (f'{wpis["kierowcow"]} kierowców, '
                        f'{wpis["wjazdow"]} wpisów historii')
                tk.Label(karta, text=opis, bg=B["tlo3"], fg=B["tekst"],
                         font=("Segoe UI Semibold", 10),
                         anchor="w").pack(anchor="w")
                sciezka = wpis["katalog"]
                if len(sciezka) > 62:
                    sciezka = "..." + sciezka[-59:]
                tk.Label(karta, text=sciezka, bg=B["tlo3"], fg=B["przygasz"],
                         font=("Consolas", 8), anchor="w").pack(anchor="w")
                tk.Label(karta, text="zmieniona "
                         + datetime.fromtimestamp(wpis["zmieniony"]).strftime(
                             "%d.%m.%Y %H:%M"),
                         bg=B["tlo3"], fg=B["przygasz"],
                         font=("Segoe UI", 8), anchor="w").pack(anchor="w")
                tk.Button(karta, text="Użyj tej bazy",
                          command=lambda x=wpis: uzyj(x), relief="flat", bd=0,
                          cursor="hand2", bg=B["akcent"], fg=B["naAkcencie"],
                          font=("Segoe UI Semibold", 9), padx=14, pady=6
                          ).pack(anchor="w", pady=(8, 0))
        else:
            tk.Label(r, text="Nie znalazłem bazy w OneDrive ani w Dokumentach.",
                     bg=B["tlo2"], fg=B["przygasz"], font=("Segoe UI", 10),
                     wraplength=440, justify="left").pack(anchor="w",
                                                          pady=(0, 14))

        tk.Label(r, text="INNE MOŻLIWOŚCI", bg=B["tlo2"], fg=B["zloto"],
                 font=("Segoe UI Semibold", 8)).pack(anchor="w",
                                                     pady=(14, 6))

        def wskaz():
            from tkinter import filedialog
            start = os.path.join(os.path.expanduser("~"), "OneDrive")
            if not os.path.isdir(start):
                start = os.path.expanduser("~")
            kat = filedialog.askdirectory(
                parent=w, initialdir=start,
                title="Wskaż katalog z bazą (albo pusty, na nową)")
            if kat:
                ustaw_katalog_danych(kat)
                self.log("wskazano katalog: " + kat)
                zamknij_i_odswiez()

        def z_kopii():
            from tkinter import filedialog
            plik = filedialog.askopenfilename(
                parent=w, filetypes=[("Kopia bazy", "*.json")],
                title="Wczytaj kopię bazy")
            if not plik:
                return
            try:
                with open(plik, encoding="utf-8") as f:
                    nowa = json.load(f)
                if "kierowcy" not in nowa:
                    raise ValueError("to nie jest kopia bazy")
                zapisz(nowa)
                self.log("wczytano kopię: " + os.path.basename(plik))
                zamknij_i_odswiez()
            except (OSError, ValueError, json.JSONDecodeError) as e:
                messagebox.showwarning("Kopia", "Nie udało się wczytać:\n"
                                       + str(e), parent=w)

        for tekst, akcja in (("Wskaż katalog ręcznie", wskaz),
                             ("Wczytaj z pliku kopii", z_kopii),
                             ("Zacznij od pustej bazy", zamknij_i_odswiez)):
            tk.Button(r, text=tekst, command=akcja, relief="flat", bd=0,
                      cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                      font=("Segoe UI", 10), padx=16, pady=8, anchor="w"
                      ).pack(fill="x", pady=(0, 6))

        tk.Label(r, text="Możesz to zmienić później w Ustawieniach.",
                 bg=B["tlo2"], fg=B["przygasz"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(12, 0))

        w.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - w.winfo_width()) // 2
        y = self.winfo_rooty() + 60
        w.geometry(f"+{max(0, x)}+{max(0, y)}")
        return w

    def _zalogowano(self):
        self._zalogowany = True
        self.ekran_pin.destroy()
        self._buduj()
        # Po zbudowaniu okna wymuszamy rozmiar jeszcze raz — dodanie
        # widgetow potrafi zmienic geometrie i okno „schodzi” z ekranu.
        if self.d.get("start_pelny", False):
            self._wlacz_pelny_start()
            self.bind("<Escape>", lambda _e: self.pelny_ekran())
        elif not getattr(self, "_pelny", False):
            self.otworz_na_caly_ekran()
            self.after(250, self._dopilnuj_maksymalizacji)
        self._pokaz_wynik_aktualizacji()
        self._petla()
        if self._nowa_instalacja:
            self.after(400, self._pierwsze_uruchomienie)
        # Sprawdzamy sekunde po zalogowaniu — dyzurny zdazy zobaczyc panel,
        # zanim pojawi sie pytanie o nowa wersje.
        self.after(1400, self._cicha_aktualizacja)

    def zablokuj(self):
        if self.animacja:
            self.after_cancel(self.animacja)
            self.animacja = None
        for w in self.winfo_children():
            w.destroy()
        self.ekran_pin = EkranPin(self, self._pin_ok, self._zalogowano)
        self.ekran_pin.pack(fill="both", expand=True)

    # ---------------- budowa okna ----------------

    def _buduj(self):
        self.gora = tk.Frame(self, bg=B["tlo2"], height=58)
        self.gora.pack(fill="x")
        self.gora.pack_propagate(False)

        marka = tk.Frame(self.gora, bg=B["tlo2"])
        marka.pack(side="left", padx=(14, 0))
        obraz = None
        if B["welon"]:                       # tryb jasny — pelne logo poziome
            plik = zasob("logo-awf.png")
            if plik:
                try:
                    obraz = Image.open(plik).convert("RGBA")
                    h = 28
                    obraz = obraz.resize(
                        (int(obraz.width * h / obraz.height), h), Image.LANCZOS)
                except (OSError, ValueError):
                    obraz = None
        else:                                # tryb ciemny — samo godlo
            try:
                from tlo_wbudowane import godlo as godlo_z_kodu
                obraz = godlo_z_kodu()
            except ImportError:
                obraz = None
            if obraz is None:
                plik = zasob("godlo-kolo.png") or zasob("godlo-awf.png")
                if plik:
                    try:
                        obraz = Image.open(plik).convert("RGBA")
                    except (OSError, ValueError):
                        obraz = None
            if obraz is not None:
                obraz = obraz.resize((38, 38), Image.LANCZOS)
        if obraz is not None:
            podklad = Image.new("RGBA", obraz.size,
                                tuple(int(B["tlo2"][i:i + 2], 16)
                                      for i in (1, 3, 5)) + (255,))
            obraz = Image.alpha_composite(podklad, obraz.convert("RGBA"))
            self._znak = ImageTk.PhotoImage(obraz.convert("RGB"))
            tk.Label(marka, image=self._znak, bg=B["tlo2"],
                     bd=0).pack(side="left")

        podpis = tk.Frame(marka, bg=B["tlo2"])
        podpis.pack(side="left", padx=(11, 0))
        tk.Label(podpis, text=self.d.get("nazwa", NAZWA), bg=B["tlo2"],
                 fg=B["tekst"], font=("Segoe UI Semibold", 12),
                 anchor="w").pack(anchor="w")
        tk.Label(podpis, text=self.d.get("podtytul", PODTYTUL), bg=B["tlo2"],
                 fg=B["przygasz"], font=("Segoe UI", 8),
                 anchor="w").pack(anchor="w")

        self.wyb_obiekt = ttk.Combobox(
            self.gora, state="readonly", width=34,
            values=[f'{o["nazwa"]} — {o["miejsce"]}' for o in self.d["obiekty"]])
        self.wyb_obiekt.current(0)
        self.wyb_obiekt.pack(side="left", padx=14)
        self.wyb_obiekt.bind("<<ComboboxSelected>>", self._zmien_obiekt)

        self.zakl = {}
        pas = tk.Frame(self.gora, bg=B["tlo2"])
        pas.pack(side="left", padx=8)
        for klucz, tekst in self.ZAKLADKI:
            e = tk.Label(pas, text=tekst, bg=B["tlo2"], fg=B["tekst2"],
                         font=("Segoe UI Semibold", 9), padx=11, pady=8,
                         cursor="hand2")
            e.pack(side="left", padx=1)
            e.bind("<Button-1>", lambda _e, k=klucz: self.przelacz(k))
            self.zakl[klucz] = e

        narz = tk.Frame(self.gora, bg=B["tlo2"])
        narz.pack(side="right", padx=(0, 14))
        for tekst, akcja in (("Tryb jasny", self.przelacz_motyw),
                             ("Okno / pełny ekran  ·  F11", self.pelny_ekran),
                             ("Zablokuj", self.zablokuj)):
            b = tk.Label(narz, text=tekst, bg=B["tlo3"], fg=B["tekst2"],
                         font=("Segoe UI", 9), padx=10, pady=6, cursor="hand2")
            b.pack(side="left", padx=3)
            b.bind("<Button-1>", lambda _e, a=akcja: a())
            if tekst == "Tryb jasny":
                self.b_motyw = b

        self.lbl_wer_gora = tk.Label(
            self.gora, text="v" + wersja_programu(), bg=B["tlo2"], fg=B["zloto"],
            font=("Segoe UI Semibold", 9), padx=8)
        self.lbl_wer_gora.pack(side="right")

        self.tresc = tk.Frame(self, bg=B["tlo"])
        self.tresc.pack(fill="both", expand=True)

        self.widoki = {}
        self.widoki["podglad"] = self._buduj_podglad()
        for klucz in ("kierowcy", "sterownik", "historia", "ustawienia"):
            self.widoki[klucz] = tk.Frame(self.tresc, bg=B["tlo"])
            self.tlo_kampusu(self.widoki[klucz])

        self._buduj_kierowcow()
        self._buduj_sterownik()
        self._buduj_historie()
        self._buduj_ustawienia()

        stopka = tk.Frame(self, bg=B["tlo2"], height=28)
        stopka.pack(fill="x")
        stopka.pack_propagate(False)
        tk.Label(stopka, text="Marymoncka 34, 00-968 Warszawa  ·  22 834 04 31"
                              "  ·  straz@awf.edu.pl", bg=B["tlo2"],
                 fg=B["przygasz"], font=("Segoe UI", 8)).pack(side="left", padx=14)
        self.lbl_wersja = tk.Label(
            stopka, text=f"{self.d.get('nazwa', NAZWA)} {wersja_programu()}  ·  Straż Akademicka",
            bg=B["tlo2"], fg=B["przygasz"], font=("Segoe UI", 8))
        self.lbl_wersja.pack(side="right", padx=14)

        self.przelacz("podglad")
        self._zmien_obiekt()

    def zacienienie(self):
        """Ile zdjecia przykrywamy — 0 do 255, liczone z ustawien.

        W bazie trzymamy procent, bo tak jest czytelniej w pliku.
        Domyslnie 46, czyli tyle, co dotad.
        """
        proc = self.d.get("przezroczystosc_tla")
        if proc is None:
            proc = 46
        return max(0, min(100, int(proc))) * 255 // 100

    def przemaluj_tla(self):
        """Przelicza wszystkie tla po przesunieciu suwaka."""
        for etykieta in getattr(self, "_tla", []):
            try:
                if etykieta.winfo_exists():
                    etykieta._rozm = None
                    etykieta._przelicz()
            except (tk.TclError, AttributeError):
                pass
        ekran = getattr(self, "ekran_pin", None)
        try:
            if ekran is not None and ekran.winfo_exists():
                ekran._rozmiar = None
                ekran._na_zmiane()
        except tk.TclError:
            pass

    def tlo_kampusu(self, ramka):
        """Zdjecie kampusu jako tlo — to samo, co na ekranie logowania.

        Program ma wygladac jak jedna calosc: po wpisaniu PIN-u zdjecie
        zostaje, a panele leza na nim. Kadr jest przyciemniony mocniej niz
        przy logowaniu, bo tu na wierzchu jest wiecej tresci.
        """
        etykieta = tk.Label(ramka, bd=0, bg=B["tlo"])
        etykieta.place(x=0, y=0, relwidth=1, relheight=1)
        etykieta.lower()
        if not hasattr(self, "_tla"):
            self._tla = []
        self._tla.append(etykieta)

        def przelicz(_e=None):
            try:
                W, H = ramka.winfo_width(), ramka.winfo_height()
            except tk.TclError:
                return
            if W < 60 or H < 60 or getattr(etykieta, "_rozm", None) == (W, H):
                return
            etykieta._rozm = (W, H)
            obraz = None
            try:
                from tlo_wbudowane import obraz as z_kodu
                obraz = z_kodu()
            except ImportError:
                plik = zasob("logowanie-tlo.jpg")
                if plik:
                    try:
                        obraz = Image.open(plik).convert("RGB")
                    except (OSError, ValueError):
                        obraz = None
            if obraz is None:
                return
            try:
                sk = max(W / obraz.width, H / obraz.height) * 1.02
                n = obraz.resize((max(W, int(obraz.width * sk)),
                                  max(H, int(obraz.height * sk))), Image.LANCZOS)
                lx = max(0, (n.width - W) // 2)
                ly = max(0, int((n.height - H) * 0.42))
                kadr = n.crop((lx, ly, lx + W, ly + H)).convert("RGBA")
                # Krycie dobrane pomiarem: przy 214 zdjecie znikalo pod
                # Przezroczystosc ustawia uzytkownik w Ustawieniach:
                # 0 = zdjecie ostre i pelne, 100 = calkiem zgaszone.
                # Panele z trescia sa nieprzezroczyste, wiec czytelnosc
                # danych nie zalezy od tego suwaka.
                zac = self.zacienienie()
                moc = 0.16 + zac / 255 * 0.46
                kryjacy = ((244, 248, 247, zac) if B["welon"]
                           else (2, 16, 10, zac))
                kadr = Image.alpha_composite(
                    kadr, Image.new("RGBA", (W, H), kryjacy))
                # winieta: narozniki ciemniejsze, srodek jasniejszy
                win = Image.new("L", (W, H), 0)
                ImageDraw.Draw(win).ellipse(
                    [-W * 0.30, -H * 0.40, W * 1.30, H * 1.40], fill=255)
                win = win.filter(ImageFilter.GaussianBlur(
                    max(40, min(W, H) // 6))).point(
                        lambda v, m=moc: int((255 - v) * m))
                barwa_win = (255, 255, 255) if B["welon"] else (0, 0, 0)
                kadr.paste(Image.new("RGBA", (W, H), barwa_win + (255,)),
                           (0, 0), win)
                if not etykieta.winfo_exists():
                    return
                etykieta._tk = ImageTk.PhotoImage(kadr.convert("RGB"))
                etykieta.configure(image=etykieta._tk)
            except (OSError, ValueError, MemoryError, tk.TclError):
                # Okno moglo zniknac w trakcie przeliczania tla —
                # nie jest to blad, po prostu nie ma juz czego malowac.
                pass

        etykieta._przelicz = przelicz
        ramka.bind("<Configure>", przelicz, add="+")
        ramka.after(80, przelicz)
        return etykieta

    def _buduj_podglad(self):
        """Uklad podgladu: kafle obiektow po lewej, scena i polecenia po prawej.

        Wczesniej wszystko bylo malowane na zdjeciu — panele, stan i przyciski.
        Na ruchliwym zdjeciu napisy gubily sie w kostce brukowej, dlatego
        teraz zdjecie jest tylko zdjeciem, a reszta to zwykle widgety.
        """
        ram = tk.Frame(self.tresc, bg=B["tlo"])
        ram.columnconfigure(1, weight=1)
        ram.rowconfigure(0, weight=1)
        self.tlo_kampusu(ram)

        # --- lewa kolumna: kafle obiektow ---
        lewa = tk.Frame(ram, bg=B["tlo"], width=300)
        lewa.grid(row=0, column=0, sticky="ns", padx=(14, 10), pady=14)
        lewa.grid_propagate(False)
        tk.Label(lewa, text="OBIEKTY", bg=B["tlo"], fg=B["zloto"],
                 font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(0, 10))

        self.kafle = []
        for nr, o in enumerate(self.d["obiekty"]):
            k = tk.Frame(lewa, bg=B["tlo2"], highlightthickness=1,
                         highlightbackground=B["tlo2"], cursor="hand2")
            k.pack(fill="x", pady=(0, 10))
            wn = tk.Frame(k, bg=B["tlo2"], padx=16, pady=14)
            wn.pack(fill="x")
            # Sama lampka stanu — rysunki slupkow i belki byly za male,
            # zeby cokolwiek z nich wyczytac, a zasmiecaly kafel.
            lam = tk.Canvas(wn, width=16, height=16, bg=B["tlo2"],
                            highlightthickness=0)
            lam.pack(side="left", padx=(0, 14))
            kropka = lam.create_oval(2, 2, 14, 14, fill=B["ok"], outline="")
            opis = tk.Frame(wn, bg=B["tlo2"])
            opis.pack(side="left", fill="x", expand=True)
            nazwa = tk.Label(opis, text=o["nazwa"], bg=B["tlo2"], fg=B["tekst"],
                             font=("Segoe UI Semibold", 13), anchor="w")
            nazwa.pack(anchor="w")
            stan = tk.Label(opis, text="—", bg=B["tlo2"], fg=B["przygasz"],
                            font=("Segoe UI", 10), anchor="w")
            stan.pack(anchor="w")
            for widget in (k, wn, lam, opis, nazwa, stan):
                widget.bind("<Button-1>", lambda _e, n=nr: self.otworz_obiekt(n))
                widget.bind("<Double-Button-1>",
                            lambda _e, n=nr: (self.wybierz_obiekt(n),
                                              self.pokaz_scene(True)))
                widget.bind("<Button-3>",
                            lambda e, n=nr: self.menu_obiektu(e, n))
                widget.bind("<Enter>", lambda _e, n=nr: self._podswietl(n, True))
                widget.bind("<Leave>", lambda _e, n=nr: self._podswietl(n, False))
            self.kafle.append({"ramka": k, "lampka": lam, "kropka": kropka,
                               "nazwa": nazwa, "stan": stan,
                               "tlo": (k, wn, lam, opis, nazwa, stan)})

        # --- prawa strona: ekran glowny albo karta wybranego obiektu ---
        # Domyslnie widac sam kampus i przeglad wszystkich obiektow. Karta
        # konkretnego szlabanu wchodzi dopiero po kliknieciu kafla i zamyka
        # sie krzyzykiem — jak okno, a nie jak stan, w ktorym sie utknie.
        self.prawa_ramka = tk.Frame(ram, bg=B["tlo"])
        self.prawa_ramka.grid(row=0, column=1, sticky="nsew",
                              padx=(0, 14), pady=14)
        self.prawa_ramka.rowconfigure(0, weight=1)
        self.prawa_ramka.columnconfigure(0, weight=1)

        self.ekran_ogolny = tk.Frame(self.prawa_ramka, bg=B["tlo"])
        self.ekran_ogolny.grid(row=0, column=0, sticky="nsew")
        self.tlo_kampusu(self.ekran_ogolny)
        self._buduj_ekran_ogolny(self.ekran_ogolny)

        prawa = tk.Frame(self.prawa_ramka, bg=B["tlo2"], highlightthickness=1,
                         highlightbackground=B["zloto2"])
        self.karta_obiektu = prawa
        prawa.rowconfigure(1, weight=1)
        prawa.columnconfigure(0, weight=1)
        self.obiekt_otwarty = False

        gora = tk.Frame(prawa, bg=B["tlo2"], padx=18, pady=14)
        gora.grid(row=0, column=0, sticky="ew")
        self.lam_stan = tk.Canvas(gora, width=18, height=18, bg=B["tlo2"],
                                  highlightthickness=0)
        self.lam_stan.pack(side="left", padx=(0, 12))
        self._kropka_stan = self.lam_stan.create_oval(2, 2, 16, 16,
                                                      fill=B["ok"], outline="")
        self.lbl_obiekt = tk.Label(gora, text="", bg=B["tlo2"], fg=B["tekst"],
                                   font=("Segoe UI Semibold", 20))
        self.lbl_obiekt.pack(side="left")
        self.lbl_stan = tk.Label(gora, text="", bg=B["tlo3"], fg=B["tekst"],
                                 font=("Segoe UI Semibold", 11), padx=16, pady=6)
        self.lbl_stan.pack(side="right")
        zamknij = tk.Label(gora, text="✕", bg=B["tlo2"], fg=B["przygasz"],
                           font=("Segoe UI", 17), cursor="hand2", padx=10)
        zamknij.pack(side="right")
        zamknij.bind("<Button-1>", lambda _e: self.zamknij_obiekt())
        zamknij.bind("<Enter>", lambda _e: zamknij.configure(fg=B["alarm"]))
        zamknij.bind("<Leave>", lambda _e: zamknij.configure(fg=B["przygasz"]))

        self.lbl_miejsce = tk.Label(gora, text="", bg=B["tlo2"],
                                    fg=B["przygasz"], font=("Segoe UI", 11))
        self.lbl_miejsce.pack(side="right", padx=14)

        # --- srodek: podsumowanie na tle kampusu, scena dopiero na zadanie ---
        # Zdjecie obiektu zajmowalo caly ekran i zaslanialo tlo. Teraz
        # domyslnie widac tlo i liczby, a scena z animacja wchodzi dopiero,
        # gdy wejdziesz w obiekt albo wydasz polecenie.
        self.srodek = tk.Frame(prawa, bg=B["tlo2"])
        self.srodek.grid(row=1, column=0, sticky="nsew", padx=18)
        self.srodek.rowconfigure(0, weight=1)
        self.srodek.columnconfigure(0, weight=1)

        self.podsumowanie = tk.Frame(self.srodek, bg=B["tlo2"])
        self.podsumowanie.grid(row=0, column=0, sticky="nsew")
        self.tlo_kampusu(self.podsumowanie)

        srod = tk.Frame(self.podsumowanie, bg=B["tlo2"], padx=30, pady=26,
                        highlightthickness=1, highlightbackground=B["zloto2"])
        srod.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_duzy = tk.Label(srod, text="", bg=B["tlo2"], fg=B["tekst"],
                                 font=("Segoe UI Semibold", 30))
        self.lbl_duzy.pack()
        self.lbl_duzy_stan = tk.Label(srod, text="", bg=B["tlo2"],
                                      font=("Segoe UI Semibold", 15))
        self.lbl_duzy_stan.pack(pady=(6, 20))

        liczby = tk.Frame(srod, bg=B["tlo2"])
        liczby.pack()
        self.liczniki = {}
        for kol, (klucz, opis) in enumerate(
                (("wjazdy", "wjazdów dziś"), ("ostatni", "ostatni przejazd"),
                 ("sterownik", "sterownik"), ("kierowcy", "uprawnionych"))):
            k = tk.Frame(liczby, bg=B["tlo2"], padx=20)
            k.grid(row=0, column=kol)
            war = tk.Label(k, text="—", bg=B["tlo2"], fg=B["tekst"],
                           font=("Segoe UI Semibold", 22))
            war.pack()
            tk.Label(k, text=opis, bg=B["tlo2"], fg=B["przygasz"],
                     font=("Segoe UI", 11)).pack()
            self.liczniki[klucz] = war

        tk.Button(srod, text="Pokaż podgląd obiektu", relief="flat", bd=0,
                  cursor="hand2", font=("Segoe UI Semibold", 13),
                  bg=B["tlo3"], fg=B["tekst"], activebackground=B["linia"],
                  padx=26, pady=13,
                  command=self.pokaz_scene).pack(pady=(24, 0))

        self.scena = Scena(self.srodek)
        self.scena.czysta = True
        self.scena.material = self.scena.wczytaj_material()
        self.scena.on_przycisk = self.przycisk_sceny
        self.scena.bind("<Button-3>",
                        lambda e: self.menu_obiektu(e, self.obiekt))
        self.scena_widoczna = False

        dol = tk.Frame(prawa, bg=B["tlo2"], padx=18, pady=16)
        dol.grid(row=2, column=0, sticky="ew")
        for i in range(5):
            dol.columnconfigure(i, weight=1, uniform="polecenia")
        self.polecenia = []
        opisy = [("Wpuść pojazd", 0, True), ("Otwórz na stałe", 1, False),
                 ("Zamknij", 2, False), ("Blokada", 3, False),
                 ("Podgląd z animacją", 4, False)]
        for kol, (tekst, nr, glowny) in enumerate(opisy):
            b = tk.Button(
                dol, text=tekst, relief="flat", bd=0, cursor="hand2",
                font=("Segoe UI Semibold", 14), pady=18,
                bg=B["zloto"] if glowny else B["tlo3"],
                fg=B["naPanelu"] if not glowny else "#16301f",
                activebackground=B["zloto2"] if glowny else B["linia"],
                activeforeground=B["tekst"] if not glowny else "#16301f",
                command=(self.przelacz_scene if nr == 4
                         else lambda n=nr: self.przycisk_sceny(n)))
            b.grid(row=0, column=kol, sticky="ew", padx=6)
            self.polecenia.append(b)
        return ram

    def _podswietl(self, nr, wchodzi):
        """Kafel pod kursorem jasnieje — widac, w co sie kliknie."""
        k = self.kafle[nr]
        if nr == self.obiekt:
            return
        tlo = B["linia"] if wchodzi else B["tlo2"]
        for w in k["tlo"]:
            try:
                w.configure(bg=tlo)
            except tk.TclError:
                pass

    def menu_obiektu(self, zdarzenie, nr):
        """Menu podreczne pod prawym klawiszem — polecenia dla tego obiektu.

        Pozycje zmieniaja sie razem ze stanem: nie ma sensu pokazywac
        "Otworz na stale", gdy juz jest otwarte na stale.
        """
        self.wybierz_obiekt(nr)
        o = self.d["obiekty"][nr]
        s = self.stany[o["id"]]
        otwarte = s["postep"] < 0.5
        stale = s.get("faza") == "otwarty_staly"

        m = tk.Menu(self, tearoff=0, bg=B["tlo2"], fg=B["tekst"],
                    activebackground=B["akcent"], activeforeground="#ffffff",
                    bd=0, font=("Segoe UI", 11))
        m.add_command(label=f'  {o["nazwa"]}  ·  {o["miejsce"]}',
                      state="disabled")
        m.add_separator()
        if not s["blokada"]:
            m.add_command(label="Wpuść pojazd",
                          command=lambda: self.przycisk_sceny(0),
                          state="disabled" if otwarte else "normal")
            m.add_command(label="Otwórz na stałe",
                          command=lambda: self.przycisk_sceny(1),
                          state="disabled" if stale else "normal")
            m.add_command(label="Zamknij" if o["typ"] == "slupki" else "Opuść",
                          command=lambda: self.przycisk_sceny(2),
                          state="normal" if (otwarte or stale) else "disabled")
            m.add_separator()
        m.add_command(
            label="Zdejmij blokadę" if s["blokada"] else "Załóż blokadę",
            command=lambda: self.przycisk_sceny(3))
        m.add_separator()
        m.add_command(label="Podgląd obiektu",
                      command=lambda: self.pokaz_scene(True))
        m.add_command(label="Animacja w osobnym oknie",
                      command=lambda: self.okno_animacji("Podgląd"))
        m.add_command(label="Historia tego obiektu",
                      command=lambda: self.przelacz("historia"))
        try:
            m.tk_popup(zdarzenie.x_root, zdarzenie.y_root)
        finally:
            m.grab_release()

    def _znaczek(self, plotno, typ):
        """Maly rysunek obiektu na kaflu. Zwraca element, ktory zmienia barwe
        razem ze stanem — dla slupkow srodkowy slupek, dla szlabanu belka."""
        if typ == "slupki":
            plotno.create_rectangle(4, 30, 40, 34, fill=B["linia"], outline="")
            for x in (9, 20, 31):
                plotno.create_rectangle(x, 12, x + 6, 30, fill=B["przygasz"],
                                        outline="")
            return plotno.create_rectangle(20, 12, 26, 30, fill=B["ok"],
                                           outline="")
        plotno.create_rectangle(4, 30, 40, 34, fill=B["linia"], outline="")
        plotno.create_rectangle(7, 12, 12, 31, fill=B["przygasz"], outline="")
        return plotno.create_line(12, 15, 40, 15, width=5, fill=B["ok"])

    def _buduj_ekran_ogolny(self, ram):
        """Ekran glowny: kampus i przeglad wszystkich obiektow naraz."""
        karta = tk.Frame(ram, bg=B["tlo2"], padx=34, pady=28,
                         highlightthickness=1, highlightbackground=B["zloto2"])
        karta.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(karta, text=NAZWA, bg=B["tlo2"], fg=B["zloto"],
                 font=("Segoe UI Semibold", 26)).pack()
        tk.Label(karta, text="Wybierz obiekt z listy po lewej, żeby nim "
                             "sterować", bg=B["tlo2"], fg=B["przygasz"],
                 font=("Segoe UI", 12)).pack(pady=(4, 22))

        rzad = tk.Frame(karta, bg=B["tlo2"])
        rzad.pack()
        self.przeglad = []
        for nr, o in enumerate(self.d["obiekty"]):
            k = tk.Frame(rzad, bg=B["tlo3"], padx=22, pady=18, cursor="hand2",
                         highlightthickness=1, highlightbackground=B["tlo3"])
            k.grid(row=0, column=nr, padx=8)
            plot = tk.Canvas(k, width=20, height=20, bg=B["tlo3"],
                             highlightthickness=0)
            plot.pack()
            znak = plot.create_oval(3, 3, 17, 17, fill=B["ok"], outline="")
            nazwa = tk.Label(k, text=o["nazwa"], bg=B["tlo3"], fg=B["tekst"],
                             font=("Segoe UI Semibold", 14))
            nazwa.pack(pady=(10, 0))
            stan = tk.Label(k, text="—", bg=B["tlo3"],
                            font=("Segoe UI Semibold", 11))
            stan.pack()
            licz = tk.Label(k, text="", bg=B["tlo3"], fg=B["przygasz"],
                            font=("Segoe UI", 10))
            licz.pack(pady=(6, 0))
            for w in (k, plot, nazwa, stan, licz):
                w.bind("<Button-1>", lambda _e, n=nr: self.otworz_obiekt(n))
            self.przeglad.append({"ramka": k, "plot": plot, "znak": znak,
                                  "stan": stan, "licz": licz,
                                  "tlo": (k, plot, nazwa, stan, licz)})

        tk.Label(karta, text="Kliknij obiekt, żeby otworzyć jego podgląd",
                 bg=B["tlo2"], fg=B["przygasz"],
                 font=("Segoe UI", 11)).pack(pady=(22, 0))

    def odswiez_przeglad(self):
        """Stany na ekranie glownym — liczone dla wszystkich obiektow."""
        if not hasattr(self, "przeglad") or self.obiekt_otwarty:
            return
        dzis = datetime.now().strftime("%Y-%m-%d")
        for nr, p in enumerate(self.przeglad):
            o = self.d["obiekty"][nr]
            st = self.stany[o["id"]]
            if st["blokada"]:
                barwa, opis = B["alarm"], "BLOKADA"
            elif st["postep"] < 0.5:
                barwa, opis = B["ok"], "OTWARTE"
            else:
                barwa, opis = B["alarm"], "ZAMKNIĘTE"
            try:
                p["plot"].itemconfigure(p["znak"], fill=barwa)
            except tk.TclError:
                pass
            p["stan"].configure(text=opis, fg=barwa)
            ile = sum(1 for h in self.d.get("historia", [])
                      if h.get("obiekt") == o["id"]
                      and str(h.get("kiedy", "")).startswith(dzis))
            p["licz"].configure(text=f"{ile} wjazdów dziś")

    def otworz_obiekt(self, nr):
        """Wejscie w obiekt — karta zaslania ekran glowny."""
        self.wybierz_obiekt(nr)
        if not self.obiekt_otwarty:
            self.ekran_ogolny.grid_remove()
            self.karta_obiektu.grid(row=0, column=0, sticky="nsew")
            self.obiekt_otwarty = True
        self.odswiez_kafle()

    def zamknij_obiekt(self):
        """Krzyzyk — wracamy do ekranu glownego z tlem kampusu."""
        if not self.obiekt_otwarty:
            return
        self.pokaz_scene(False)
        self.karta_obiektu.grid_remove()
        self.ekran_ogolny.grid(row=0, column=0, sticky="nsew")
        self.obiekt_otwarty = False
        self.odswiez_przeglad()
        self.log("zamknięto podgląd obiektu")

    def pokaz_scene(self, pokaz=True):
        """Przelacza srodek miedzy podsumowaniem a scena z animacja."""
        if not hasattr(self, "scena_widoczna"):
            return
        if pokaz and not self.scena_widoczna:
            self.podsumowanie.grid_remove()
            self.scena.grid(row=0, column=0, sticky="nsew")
            self.scena_widoczna = True
            self.scena.rysuj()
            self.polecenia[4].configure(text="Ukryj animację")
        elif not pokaz and self.scena_widoczna:
            self.scena.grid_remove()
            self.podsumowanie.grid()
            self.scena_widoczna = False
            self.polecenia[4].configure(text="Podgląd z animacją")

    def przelacz_scene(self):
        self.pokaz_scene(not self.scena_widoczna)

    def odswiez_liczby(self):
        """Liczby w podsumowaniu — tylko gdy podsumowanie jest widoczne."""
        if not hasattr(self, "liczniki") or self.scena_widoczna:
            return
        o = self.d["obiekty"][self.obiekt]
        wpisy = [h for h in self.d.get("historia", [])
                 if h.get("obiekt") == o["id"]]
        dzis = datetime.now().strftime("%Y-%m-%d")
        self.liczniki["wjazdy"].configure(
            text=str(sum(1 for h in wpisy if str(h.get("kiedy", "")).startswith(dzis))))
        ostatni = wpisy[-1].get("kiedy", "") if wpisy else ""
        self.liczniki["ostatni"].configure(text=(ostatni[11:16] or "—"))
        polaczony = self.d.get("sterowniki", {}).get(o["id"], {}).get(
            "stan", "połączony")
        self.liczniki["sterownik"].configure(
            text="łączy" if polaczony != "brak" else "brak",
            fg=B["ok"] if polaczony != "brak" else B["alarm"])
        self.liczniki["kierowcy"].configure(
            text=str(sum(1 for k in self.d["kierowcy"] if k.get("aktywny", True))))

    def wybierz_obiekt(self, nr):
        """Klikniecie w kafel obiektu."""
        if nr == self.obiekt:
            return
        if hasattr(self, "wyb_obiekt"):
            self.wyb_obiekt.current(nr)
        self._zmien_obiekt(wybrany=nr)

    def odswiez_kafle(self):
        """Lampki i napisy na kaflach oraz plakietka stanu nad scena."""
        if not hasattr(self, "kafle"):
            return
        opis, kolor = self.scena._stan()
        for nr, k in enumerate(self.kafle):
            wybrany = nr == self.obiekt
            tlo = B["tlo3"] if wybrany else B["tlo2"]
            for w in k["tlo"]:
                try:
                    w.configure(bg=tlo)
                except tk.TclError:
                    pass
            k["ramka"].configure(highlightbackground=B["zloto"] if wybrany else tlo)
            o = self.d["obiekty"][nr]
            s = self.stany[o["id"]]
            if wybrany:
                barwa, tekst = kolor, opis
            elif s["blokada"]:
                barwa, tekst = B["alarm"], "BLOKADA"
            elif s["postep"] < 0.5:
                barwa, tekst = B["ok"], "OTWARTE"
            else:
                barwa, tekst = B["alarm"], "ZAMKNIĘTE"
            try:
                k["lampka"].itemconfigure(k["kropka"], fill=barwa)
            except tk.TclError:
                pass
            k["stan"].configure(text=tekst.capitalize(), fg=barwa)
        self.lam_stan.itemconfigure(self._kropka_stan, fill=kolor)
        self.lbl_stan.configure(text=opis, fg=kolor)
        if hasattr(self, "lbl_duzy"):
            self.lbl_duzy.configure(text=self.d["obiekty"][self.obiekt]["nazwa"])
            self.lbl_duzy_stan.configure(text=opis, fg=kolor)
            self.odswiez_liczby()
        self.polecenia[2].configure(
            text="Zamknij" if self.scena.typ == "slupki" else "Opuść")
        self.polecenia[3].configure(
            text="Zdejmij blokadę" if self.scena.zablokowana else "Blokada")

    def przelacz(self, klucz):
        for w in self.widoki.values():
            w.pack_forget()
        self.widoki[klucz].pack(fill="both", expand=True)
        for k, e in self.zakl.items():
            e.configure(bg=B["tlo3"] if k == klucz else B["tlo2"],
                        fg=B["tekst"] if k == klucz else B["tekst2"])
        if klucz == "podglad":
            self.after(30, self.scena.rysuj)
        elif klucz == "kierowcy":
            self.odswiez_kierowcow()
        elif klucz == "historia":
            self.odswiez_historie()

    # ---------------- zakladki ----------------

    def _naglowek(self, rodzic, tytul, podtytul):
        """Naglowek zakladki — zlota kreska z lewej porzadkuje kolumne."""
        r = tk.Frame(rodzic, bg=B["tlo2"])
        r.pack(fill="x", padx=24, pady=(22, 16))
        kreska = tk.Frame(r, bg=B["zloto"], width=4)
        kreska.pack(side="left", fill="y")
        opis = tk.Frame(r, bg=B["tlo2"], padx=18, pady=14)
        opis.pack(side="left", fill="x", expand=True)
        tk.Label(opis, text=tytul, bg=B["tlo2"], fg=B["tekst"],
                 font=("Segoe UI Semibold", 20)).pack(anchor="w")
        tk.Label(opis, text=podtytul, bg=B["tlo2"], fg=B["przygasz"],
                 font=("Segoe UI", 12)).pack(anchor="w", pady=(3, 0))

    def _tabela(self, rodzic, kolumny, szerokosci):
        """Tabela osadzona w karcie ze zlota obwodka."""
        karta = tk.Frame(rodzic, bg=B["tlo2"], highlightthickness=1,
                         highlightbackground=B["zloto2"])
        karta.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        ram = tk.Frame(karta, bg=B["tlo2"], padx=14, pady=14)
        ram.pack(fill="both", expand=True)
        styl = ttk.Style()
        styl.theme_use("clam")
        styl.configure("AWF.Treeview", background=B["tlo2"],
                       fieldbackground=B["tlo2"], foreground=B["tekst"],
                       rowheight=42, borderwidth=0,
                       font=("Segoe UI", 12))
        styl.configure("AWF.Treeview.Heading", background=B["tlo2"],
                       foreground=B["zloto"], relief="flat", padding=(6, 10),
                       font=("Segoe UI Semibold", 10))
        styl.map("AWF.Treeview", background=[("selected", B["akcent2"])],
                 foreground=[("selected", "#ffffff")])
        t = ttk.Treeview(ram, columns=kolumny, show="headings",
                         style="AWF.Treeview")
        for k, sz in zip(kolumny, szerokosci):
            t.heading(k, text=k.upper())
            t.column(k, width=sz, anchor="w")
        pion = ttk.Scrollbar(ram, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=pion.set)
        t.pack(side="left", fill="both", expand=True)
        pion.pack(side="right", fill="y")
        t.tag_configure("ok", foreground=B["ok"])
        t.tag_configure("uwaga", foreground=B["uwaga"])
        t.tag_configure("alarm", foreground=B["alarm"])
        return t

    def _przyciski(self, rodzic, pozycje):
        r = tk.Frame(rodzic, bg=B["tlo2"])
        r.pack(fill="x", padx=24, pady=(0, 20), ipady=10, ipadx=10)
        for tekst, akcja, glowny in pozycje:
            tk.Button(r, text=tekst, command=akcja, relief="flat", bd=0,
                      cursor="hand2", font=("Segoe UI Semibold", 13),
                      padx=26, pady=13,
                      bg=B["zloto"] if glowny else B["tlo3"],
                      fg="#16301f" if glowny else B["tekst"],
                      activebackground=B["zloto2"] if glowny else B["linia"],
                      activeforeground="#16301f" if glowny else B["tekst"]
                      ).pack(side="left", padx=(0, 10))

    def _buduj_kierowcow(self):
        w = self.widoki["kierowcy"]
        self._naglowek(w, "Kierowcy uprawnieni",
                       "Stan liczy się na bieżąco z harmonogramu i daty ważności")
        self.tab_kier = self._tabela(
            w, ("kierowca", "rola", "telefon", "harmonogram", "ważny do",
                "wjazdów", "stan"),
            (200, 150, 140, 190, 100, 80, 110))
        self.tab_kier.bind("<<TreeviewSelect>>", self._wybor_kierowcy)
        self._przyciski(w, [("Dodaj", lambda: self.okno_kierowcy(None), True),
                            ("Edytuj", lambda: self.okno_kierowcy(self.wybrany), False),
                            ("Usuń", self.usun_kierowce, False)])

    def odswiez_kierowcow(self):
        for i in self.tab_kier.get_children():
            self.tab_kier.delete(i)
        for i, k in enumerate(self.d["kierowcy"]):
            ok, powod = sprawdz_dostep(k)
            if not k.get("aktywny", True):
                stan, tag = "ZABLOKOWANY", "alarm"
            elif ok:
                stan, tag = "wpuszcza", "ok"
            else:
                stan, tag = powod, "uwaga"
            self.tab_kier.insert(
                "", "end", iid=str(i),
                values=(k["imie"], k.get("rola", ""), k["tel"],
                        opis_harmonogramu(k), k.get("wazny") or "—",
                        k.get("ile", 0), stan), tags=(tag,))

    def _wybor_kierowcy(self, _=None):
        sel = self.tab_kier.selection()
        if sel:
            self.wybrany = int(sel[0])

    def _buduj_sterownik(self):
        w = self.widoki["sterownik"]
        self._naglowek(w, "Moduł przy bramie", "ESP32 z modemem LTE")
        karty = tk.Frame(w, bg=B["tlo"])
        karty.pack(fill="x", padx=24, pady=(0, 16))
        self.karty_ster = {}
        for etykieta in ("Łączność", "Sygnał", "Sieć", "Czas pracy", "Zasilanie"):
            k = tk.Frame(karty, bg=B["tlo2"], highlightthickness=1,
                         highlightbackground=B["linia"])
            k.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(k, text=etykieta.upper(), bg=B["tlo2"], fg=B["przygasz"],
                     font=("Segoe UI", 10), anchor="w").pack(anchor="w", padx=14,
                                                            pady=(12, 0))
            v = tk.Label(k, text="—", bg=B["tlo2"], fg=B["akcent"],
                         font=("Segoe UI Semibold", 13), anchor="w")
            v.pack(anchor="w", padx=14, pady=(2, 12))
            self.karty_ster[etykieta] = v
        for e, t in (("Łączność", "połączony"), ("Sygnał", "77%"),
                     ("Sieć", "LTE · Play"), ("Czas pracy", "14 d 6 h"),
                     ("Zasilanie", "12.3 V")):
            self.karty_ster[e].configure(text=t)

        tk.Label(w, text="DZIENNIK", bg=B["tlo"], fg=B["przygasz"],
                 font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=24)
        self.dziennik = tk.Text(w, height=14, bg="#050d09" if not B["welon"]
                                else "#f7faf8", fg=B["tekst2"], relief="flat",
                                font=("Consolas", 9), padx=12, pady=8)
        self.dziennik.pack(fill="both", expand=True, padx=24, pady=(4, 16))
        self.dziennik.configure(state="disabled")

    def _buduj_historie(self):
        w = self.widoki["historia"]
        self._naglowek(w, "Historia wjazdów", "Zapisywana w programie i w module")
        self.tab_hist = self._tabela(
            w, ("data", "godzina", "kierowca", "telefon", "obiekt", "sposób"),
            (110, 90, 210, 150, 220, 240))
        self._przyciski(w, [("Raport do wydruku", self.raport, True),
                            ("Wyczyść starsze niż rok", self.czysc_historie, False)])

    def odswiez_historie(self):
        for i in self.tab_hist.get_children():
            self.tab_hist.delete(i)
        for w in reversed(self.d.get("historia", [])[-300:]):
            tag = ("alarm" if w.get("sposob", "").startswith("ODMOWA")
                   else ("uwaga" if "ręczne" in w.get("sposob", "") else ""))
            self.tab_hist.insert("", "end", values=(
                w.get("data", ""), w.get("godzina", ""), w.get("imie", ""),
                w.get("tel", ""), w.get("obiekt", ""), w.get("sposob", "")),
                tags=(tag,) if tag else ())

    def _buduj_ustawienia(self):
        w = self.widoki["ustawienia"]
        self._naglowek(w, "Ustawienia", "Zmiany zapisują się od razu")
        r = tk.Frame(w, bg=B["tlo2"], highlightthickness=1,
                     highlightbackground=B["linia"])
        r.pack(fill="x", padx=24, pady=(0, 16))
        siatka = tk.Frame(r, bg=B["tlo2"], padx=18, pady=16)
        siatka.pack(fill="x")

        tk.Label(siatka, text="NAZWA SYSTEMU", bg=B["tlo2"], fg=B["przygasz"],
                 font=("Segoe UI Semibold", 8)).grid(row=0, column=0,
                                                     sticky="w", pady=(0, 6))
        self.pole_nazwa = tk.Entry(siatka, bg=B["tlo3"], fg=B["tekst"],
                                   relief="flat", font=("Segoe UI", 12),
                                   insertbackground=B["tekst"], width=28)
        self.pole_nazwa.insert(0, self.d.get("nazwa", NAZWA))
        self.pole_nazwa.grid(row=1, column=0, sticky="w", ipady=5, padx=(0, 10))
        self.pole_podtytul = tk.Entry(siatka, bg=B["tlo3"], fg=B["tekst"],
                                      relief="flat", font=("Segoe UI", 12),
                                      insertbackground=B["tekst"], width=34)
        self.pole_podtytul.insert(0, self.d.get("podtytul", PODTYTUL))
        self.pole_podtytul.grid(row=1, column=1, sticky="w", ipady=5, padx=(0, 10))
        tk.Button(siatka, text="Zastosuj", command=self.zmien_nazwe,
                  relief="flat", bd=0, cursor="hand2", bg=B["akcent"],
                  fg=B["naAkcencie"], font=("Segoe UI", 12), padx=16, pady=6
                  ).grid(row=1, column=2, sticky="w")

        # --- gdzie trzymac baze ---
        r2 = tk.Frame(w, bg=B["tlo2"], highlightthickness=1,
                      highlightbackground=B["linia"])
        r2.pack(fill="x", padx=24, pady=(0, 16))
        s2 = tk.Frame(r2, bg=B["tlo2"], padx=18, pady=16)
        s2.pack(fill="x")
        tk.Label(s2, text="GDZIE TRZYMAĆ BAZĘ NUMERÓW", bg=B["tlo2"],
                 fg=B["przygasz"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(s2, text="Wskaż katalog w OneDrive, a ta sama baza będzie "
                          "widoczna na każdym komputerze, gdzie zainstalujesz "
                          "program. Nic nie trzeba wpisywać drugi raz.",
                 bg=B["tlo2"], fg=B["przygasz"], font=("Segoe UI", 11),
                 wraplength=760, justify="left").pack(anchor="w", pady=(4, 10))
        self.lbl_katalog = tk.Label(
            s2, text=katalog_danych(), bg=B["tlo3"], fg=B["tekst"],
            font=("Consolas", 9), anchor="w", padx=10, pady=7)
        self.lbl_katalog.pack(fill="x")
        pk = tk.Frame(s2, bg=B["tlo2"])
        pk.pack(anchor="w", pady=(10, 0))
        for tekst, akcja, glowny in (
                ("Wskaż katalog w OneDrive", self.wybierz_katalog, True),
                ("Wróć do domyślnego", self.katalog_domyslny_wroc, False),
                ("Otwórz katalog", self.otworz_katalog, False)):
            tk.Button(pk, text=tekst, command=akcja, relief="flat", bd=0,
                      cursor="hand2", font=("Segoe UI", 12), padx=14, pady=7,
                      bg=B["akcent"] if glowny else B["tlo3"],
                      fg=B["naAkcencie"] if glowny else B["tekst"],
                      activebackground=B["zloto"] if glowny else B["linia"]
                      ).pack(side="left", padx=(0, 8))

        v_pelny = tk.BooleanVar(value=self.d.get("start_pelny", False))

        def zmien_start():
            self.d["start_pelny"] = v_pelny.get()
            zapisz(self.d)
            self.log("start na pełnym ekranie: "
                     + ("tak" if v_pelny.get() else "nie"))

        tk.Checkbutton(w, text="Otwieraj bez ramki, na cały ekran "
                               "(tryb dyżurki)  ·  wyjście klawiszem Escape",
                       variable=v_pelny, command=zmien_start, bg=B["tlo"],
                       fg=B["tekst"], selectcolor=B["tlo3"],
                       activebackground=B["tlo"], activeforeground=B["tekst"],
                       font=("Segoe UI", 12)).pack(anchor="w", padx=24,
                                                   pady=(0, 14))

        self._przyciski(w, [("Co nowego w kolejnych wersjach", self.okno_historii, False),
                            ("Zapisz kopię bazy", self.kopia_zapisz, False),
                            ("Wczytaj kopię", self.kopia_wczytaj, False),
                            ("Zmień PIN", self.zmien_pin, False),
                            ("Sprawdź aktualizacje", self.sprawdz_recznie, True)])
        self.lbl_akt = tk.Label(
            w, text=f"Wersja programu: {wersja_programu()}  ·  jeszcze nie sprawdzano",
            bg=B["tlo"], fg=B["przygasz"], font=("Segoe UI", 12))
        self.lbl_akt.pack(anchor="w", padx=24)
        tk.Label(w, text="Program sprawdza aktualizacje na ekranie logowania, "
                         "zanim ktokolwiek wpisze PIN. Sam decydujesz, "
                         "czy ma pytać, czy wgrywać bez pytania.",
                 bg=B["tlo"], fg=B["przygasz"],
                 font=("Segoe UI", 11)).pack(anchor="w", padx=24, pady=(4, 0))

        r_auto = tk.Frame(w, bg=B["tlo"])
        r_auto.pack(anchor="w", padx=24, pady=(10, 0))
        self.lbl_auto = tk.Label(r_auto, bg=B["tlo"], fg=B["przygasz"],
                                 font=("Segoe UI", 12))
        self.lbl_auto.pack(side="left", padx=(0, 12))

        def przelacz_auto():
            """Trzy stany po kolei: pyta → wgrywa sam → nie sprawdza."""
            teraz = self.tryb_aktualizacji()
            nowy = {"pyta": "sam", "sam": "wylaczone",
                    "wylaczone": "pyta"}[teraz]
            self.d["tryb_aktualizacji"] = nowy
            self.d.pop("sprawdzaj_aktualizacje", None)
            self.d.pop("auto_aktualizacja", None)
            zapisz(self.d)
            odswiez_auto()
            self.log("aktualizacje: " + {
                "pyta": "program pyta przed wgraniem",
                "sam": "program wgrywa sam",
                "wylaczone": "nie sprawdza"}[nowy])

        b_auto = tk.Button(r_auto, command=przelacz_auto, relief="flat", bd=0,
                           cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                           font=("Segoe UI", 12), padx=16, pady=6)
        b_auto.pack(side="left")

        def odswiez_auto():
            opis = {
                "pyta": ("Pyta przed wgraniem nowej wersji", B["ok"],
                         "Zmień na: wgrywaj sam"),
                "sam": ("Wgrywa nowe wersje sam, bez pytania", B["uwaga"],
                        "Zmień na: nie sprawdzaj"),
                "wylaczone": ("Nie sprawdza nowych wersji", B["przygasz"],
                              "Zmień na: pytaj"),
            }[self.tryb_aktualizacji()]
            self.lbl_auto.configure(text=opis[0], fg=opis[1])
            b_auto.configure(text=opis[2])

        odswiez_auto()

        r_styl = tk.Frame(w, bg=B["tlo"])
        r_styl.pack(anchor="w", padx=24, pady=(8, 0))
        lbl_styl = tk.Label(r_styl, bg=B["tlo"], fg=B["przygasz"],
                            font=("Segoe UI", 12))
        lbl_styl.pack(side="left", padx=(0, 12))

        def przelacz_styl():
            self.d["karta_logowania"] = not self.d.get("karta_logowania", False)
            zapisz(self.d)
            odswiez_styl()

            self.log("układ logowania: "
                     + ("karta" if self.d["karta_logowania"] else "bez karty"))

        b_styl = tk.Button(r_styl, command=przelacz_styl, relief="flat", bd=0,
                           cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                           font=("Segoe UI", 12), padx=16, pady=6)
        b_styl.pack(side="left")

        def odswiez_styl():
            karta = bool(self.d.get("karta_logowania", False))
            lbl_styl.configure(
                text=("Logowanie: klawiatura na karcie" if karta
                      else "Logowanie: klawiatura wprost na zdjęciu"))
            b_styl.configure(text="Pokaż kartę" if not karta else "Bez karty")

        odswiez_styl()

        # --- suwak przezroczystosci tla ---
        r_tlo = tk.Frame(w, bg=B["tlo"])
        r_tlo.pack(fill="x", padx=24, pady=(14, 0))
        naglowek_tla = tk.Frame(r_tlo, bg=B["tlo"])
        naglowek_tla.pack(fill="x")
        tk.Label(naglowek_tla, text="Przezroczystość tła", bg=B["tlo"],
                 fg=B["tekst"], font=("Segoe UI Semibold", 12)).pack(side="left")
        self.lbl_tlo = tk.Label(naglowek_tla, bg=B["tlo"], fg=B["zloto"],
                                font=("Segoe UI Semibold", 12))
        self.lbl_tlo.pack(side="right")
        tk.Label(r_tlo, text="Im mniej, tym wyraźniej widać zdjęcie kampusu. "
                             "Panele z danymi zostają czytelne niezależnie "
                             "od ustawienia.",
                 bg=B["tlo"], fg=B["przygasz"], font=("Segoe UI", 10),
                 justify="left", wraplength=560).pack(anchor="w", pady=(2, 6))

        styl_suwak = ttk.Style()
        styl_suwak.configure("AWF.Horizontal.TScale", background=B["tlo"],
                             troughcolor=B["tlo3"], borderwidth=0)
        self.suwak_tla = ttk.Scale(r_tlo, from_=0, to=100, orient="horizontal",
                                   style="AWF.Horizontal.TScale", length=560)
        self.suwak_tla.set(self.d.get("przezroczystosc_tla", 46))
        self.suwak_tla.pack(anchor="w")

        def opis_tla(proc):
            if proc <= 15:
                return "zdjęcie w pełni"
            if proc <= 40:
                return "zdjęcie wyraźne"
            if proc <= 65:
                return "wyważone"
            if proc <= 85:
                return "zdjęcie przygaszone"
            return "prawie jednolite tło"

        def przesun(_=None):
            proc = int(round(float(self.suwak_tla.get())))
            self.lbl_tlo.configure(text=f"{proc}%  ·  {opis_tla(proc)}")
            if self.d.get("przezroczystosc_tla") == proc:
                return
            self.d["przezroczystosc_tla"] = proc
            # przemalowanie jest kosztowne, wiec czekamy az suwak stanie
            if getattr(self, "_zad_tlo", None):
                self.after_cancel(self._zad_tlo)
            self._zad_tlo = self.after(220, self._zastosuj_tlo)

        self.suwak_tla.configure(command=przesun)
        przesun()

        # --- lista stylow graficznych ---
        r_styl2 = tk.Frame(w, bg=B["tlo"])
        r_styl2.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(r_styl2, text="Styl graficzny", bg=B["tlo"], fg=B["tekst"],
                 font=("Segoe UI Semibold", 12)).pack(anchor="w")
        tk.Label(r_styl2, text="Dwanaście palet barw. Zmiana działa od razu "
                                "i zapisuje się w bazie.",
                 bg=B["tlo"], fg=B["przygasz"], font=("Segoe UI", 10)
                 ).pack(anchor="w", pady=(2, 8))

        siatka_st = tk.Frame(r_styl2, bg=B["tlo"])
        siatka_st.pack(anchor="w")
        biezacy = self.d.get("styl", 3)
        for nr, (nazwa, paleta) in sorted(STYLE.items()):
            kol, wier = (nr - 1) % 4, (nr - 1) // 4
            k = tk.Frame(siatka_st, bg=B["tlo2"], cursor="hand2",
                         highlightthickness=2,
                         highlightbackground=B["zloto"] if nr == biezacy
                         else B["tlo"])
            k.grid(row=wier, column=kol, padx=(0, 8), pady=(0, 8), sticky="ew")
            # probka trzech barw stylu — widac, co sie wybiera
            probka = tk.Frame(k, bg=B["tlo2"])
            probka.pack(fill="x", padx=10, pady=(10, 6))
            for barwa in (paleta["tlo"], paleta["tlo3"], paleta["zloto"]):
                tk.Frame(probka, bg=barwa, width=26, height=22).pack(side="left")
            tk.Label(k, text=f"{nr} · {nazwa}", bg=B["tlo2"],
                     fg=B["zloto"] if nr == biezacy else B["tekst"],
                     font=("Segoe UI Semibold", 10)).pack(anchor="w", padx=10,
                                                          pady=(0, 10))
            for widget in (k, probka) + tuple(probka.winfo_children()):
                widget.bind("<Button-1>", lambda _e, n=nr: self.zmien_styl(n))
            k.winfo_children()[-1].bind("<Button-1>",
                                        lambda _e, n=nr: self.zmien_styl(n))

        r_skroty = tk.Frame(r_tlo, bg=B["tlo"])
        r_skroty.pack(anchor="w", pady=(8, 0))
        for etykieta, wartosc in (("Zdjęcie w pełni", 8), ("Wyważone", 46),
                                  ("Przygaszone", 78), ("Bez zdjęcia", 100)):
            tk.Button(r_skroty, text=etykieta, relief="flat", bd=0,
                      cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                      activebackground=B["linia"], font=("Segoe UI", 10),
                      padx=14, pady=7,
                      command=lambda v=wartosc: (self.suwak_tla.set(v),
                                                 przesun())
                      ).pack(side="left", padx=(0, 8))
        tk.Label(w, text="Zmiana układu logowania działa od następnego "
                         "uruchomienia programu.",
                 bg=B["tlo"], fg=B["przygasz"],
                 font=("Segoe UI", 11)).pack(anchor="w", padx=24, pady=(4, 0))

    # ---------------- dzialanie ----------------

    def log(self, tekst):
        # Dziennik znika przy zablokowaniu ekranu i przy zmianie motywu.
        # Wpis do nieistniejacego pola nie moze zatrzymac programu.
        if not hasattr(self, "dziennik"):
            return
        try:
            self.dziennik.configure(state="normal")
            self.dziennik.insert("1.0", datetime.now().strftime("%H:%M:%S  ")
                                 + tekst + "\n")
            self.dziennik.configure(state="disabled")
        except tk.TclError:
            pass

    def _zmien_obiekt(self, _=None, wybrany=None):
        stary = self.d["obiekty"][self.obiekt]["id"]
        self.stany[stary] = {"postep": self.scena.postep,
                             "faza": self.scena.faza,
                             "blokada": self.scena.zablokowana}
        if wybrany is not None:
            self.obiekt = wybrany
        elif hasattr(self, "wyb_obiekt"):
            self.obiekt = self.wyb_obiekt.current()
        o = self.d["obiekty"][self.obiekt]
        s = self.stany[o["id"]]
        self.scena.typ = o["typ"]
        self.scena.nazwa_obiektu = f'{o["nazwa"]} — {o["miejsce"]}'
        self.scena.postep = s["postep"]
        self.scena.faza = s["faza"]
        self.scena.zablokowana = s["blokada"]
        self.scena.dzis = sum(
            1 for w in self.d.get("historia", [])
            if w.get("obiekt") == o["nazwa"]
            and w.get("data") == datetime.now().strftime("%d.%m.%Y"))
        self.scena._kiosk = None
        self.log(f'obiekt: {o["nazwa"]} — {o["miejsce"]}')
        if hasattr(self, "lbl_obiekt"):
            self.lbl_obiekt.configure(text=o["nazwa"])
            self.lbl_miejsce.configure(text=o["miejsce"])
        self.pokaz_scene(False)
        self.odswiez_kafle()
        self.odswiez_przeglad()
        if getattr(self, "obiekt_otwarty", False):
            self.scena.rysuj()

    def przycisk_sceny(self, nr):
        """Polecenie z przycisku — z pytaniem i sprawdzeniem stanu.

        Dwa razy tego samego nie robimy: jesli zapora jest juz otwarta na
        stale, drugie "Otworz na stale" nic nie zmieni, a wyslalo by kolejny
        impuls do sterownika i kolejny wpis do historii.
        """
        o = self.d["obiekty"][self.obiekt]
        nazwa = o["nazwa"]
        otwarte = self.scena.postep < 0.5
        stale = self.scena.faza == "otwarty_staly"

        if nr == 0:
            if self.scena.zablokowana:
                self.info_okno("Blokada założona",
                               f"{nazwa} ma założoną blokadę. Zdejmij ją, "
                               "zanim wpuścisz pojazd.")
                return
            if otwarte:
                self.info_okno("Już otwarte",
                               f"{nazwa} jest w tej chwili otwarta. "
                               "Pojazd może przejechać.")
                return
            self.wpusc()
            self.okno_animacji("Wpuszczanie pojazdu")

        elif nr == 1:
            if self.scena.zablokowana:
                self.info_okno("Blokada założona",
                               f"{nazwa} ma założoną blokadę.")
                return
            if stale:
                self.info_okno("Już otwarte na stałe",
                               f"{nazwa} jest już otwarta na stałe.")
                return
            if okno_pytania(self, "Otworzyć na stałe?",
                            f"{nazwa} zostanie otwarta i pozostanie otwarta, "
                            "dopóki jej nie zamkniesz.\n\n"
                            "Przez ten czas każdy pojazd przejedzie bez "
                            "sprawdzania numeru.",
                            tak="Otwórz na stałe", nie="Anuluj",
                            ostrzezenie=True):
                self.recznie(True)
                self.okno_animacji("Otwieranie na stałe")

        elif nr == 2:
            if not otwarte and not stale:
                self.info_okno("Już zamknięte", f"{nazwa} jest zamknięta.")
                return
            if okno_pytania(self, "Zamknąć teraz?",
                            f"{nazwa} zostanie zamknięta natychmiast.\n\n"
                            "Upewnij się, że pod zaporą nie stoi pojazd."
                            if o["typ"] == "slupki" else
                            f"{nazwa} zostanie opuszczony natychmiast.\n\n"
                            "Upewnij się, że pod belką nie stoi pojazd.",
                            tak="Zamknij", nie="Anuluj", ostrzezenie=True):
                self.recznie(False)
                self.okno_animacji("Zamykanie")

        else:
            if self.scena.zablokowana:
                if okno_pytania(self, "Zdjąć blokadę?",
                                f"{nazwa} wróci do normalnej pracy i znów "
                                "będzie przyjmować połączenia od kierowców.",
                                tak="Zdejmij blokadę", nie="Anuluj"):
                    self.blokada()
            elif okno_pytania(self, "Założyć blokadę?",
                              f"{nazwa} zostanie zamknięta, a wszystkie "
                              "połączenia od kierowców będą ignorowane.\n\n"
                              "Nikt nie wjedzie do czasu zdjęcia blokady.",
                              tak="Załóż blokadę", nie="Anuluj",
                              ostrzezenie=True):
                self.blokada()

    def okno_animacji(self, tytul):
        """Osobne okno z animacja wybranego obiektu.

        Wyskakuje po zatwierdzeniu polecenia i pokazuje, co dzieje sie na
        obiekcie — z bliska, na calym oknie. Zamyka sie samo, gdy ruch
        dobiegnie konca.
        """
        istniejace = getattr(self, "_okno_ruchu", None)
        if istniejace is not None and istniejace.winfo_exists():
            istniejace.destroy()

        o = self.d["obiekty"][self.obiekt]
        w = tk.Toplevel(self)
        self._okno_ruchu = w
        w.title(f'{o["nazwa"]} — {tytul}')
        w.configure(bg=B["tlo2"])
        w.transient(self)
        szer, wys = 900, 620
        w.geometry(f"{szer}x{wys}")

        pasek = tk.Frame(w, bg=B["tlo2"], padx=22, pady=16)
        pasek.pack(fill="x")
        tk.Label(pasek, text=o["nazwa"], bg=B["tlo2"], fg=B["tekst"],
                 font=("Segoe UI Semibold", 18)).pack(side="left")
        lbl = tk.Label(pasek, text=tytul, bg=B["tlo3"], fg=B["zloto"],
                       font=("Segoe UI Semibold", 12), padx=16, pady=7)
        lbl.pack(side="right")

        scena = Scena(w)
        scena.czysta = True
        scena.material = self.scena.material
        scena.typ = self.scena.typ
        scena.pack(fill="both", expand=True, padx=22, pady=(0, 16))

        tk.Button(w, text="Zamknij podgląd", command=w.destroy, relief="flat",
                  bd=0, cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                  activebackground=B["linia"], font=("Segoe UI", 12),
                  padx=24, pady=12).pack(pady=(0, 18))

        def odswiez():
            if not w.winfo_exists():
                return
            scena.postep = self.scena.postep
            scena.faza = self.scena.faza
            scena.zablokowana = self.scena.zablokowana
            scena.rysuj()
            opis, kolor = scena._stan()
            lbl.configure(text=opis, fg=kolor)
            if self.scena.faza in ("spoczynek", "otwarty_staly", "blokada"):
                # ruch dobiegl konca — zostawiamy okno na chwile i zamykamy
                w.after(2200, lambda: w.winfo_exists() and w.destroy())
                return
            w.after(60, odswiez)

        w.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - szer) // 2
        y = self.winfo_rooty() + (self.winfo_height() - wys) // 3
        w.geometry(f"+{max(0, x)}+{max(0, y)}")
        odswiez()
        return w

    def info_okno(self, tytul, tresc):
        """Komunikat w barwach programu — z jednym przyciskiem."""
        okno_tresci(self, tytul, [(tresc, "tekst")])

    def _ruch(self, cel, potem=None):
        if self.animacja:
            self.after_cancel(self.animacja)
        start = self.scena.postep
        czas = 1900 if cel < start else 2000
        t0 = datetime.now()

        def krok():
            u = min(1.0, (datetime.now() - t0).total_seconds() * 1000 / czas)
            g = u * u * (3 - 2 * u)
            try:
                self.scena.postep = start + (cel - start) * g
                self.scena.rysuj()
            except tk.TclError:
                self.animacja = None
                return
            if u < 1:
                self.animacja = self.after(24, krok)
            else:
                self.animacja = None
                if potem:
                    potem()
        krok()

    def wpusc(self):
        if self.scena.zablokowana:
            self.log("połączenie odrzucone — blokada")
            return
        k = self.d["kierowcy"][self.wybrany] if self.d["kierowcy"] else None
        if not k:
            return
        ok, powod = sprawdz_dostep(k)
        self.scena.kto, self.scena.tel = k["imie"], k["tel"]
        self.scena.powod = "" if ok else powod
        self.scena.faza = "dzwoni"
        self.scena.rysuj()
        self.log(f'połączenie: {k["imie"]} {k["tel"]}')

        def dalej():
            if not ok:
                self.scena.faza = "odmowa"
                self.scena.rysuj()
                self.log("ODMOWA — " + powod)
                self.zapisz_wjazd(k, "ODMOWA — " + powod)
                self.after(2600, self.wroc)
                return
            o = self.d["obiekty"][self.obiekt]
            self.scena.faza = "otwieranie"
            self.log(f'numer rozpoznany — impuls {o["impuls"]} ms')
            self.zapisz_wjazd(k, "przejazd")
            self._ruch(0.0, self.po_otwarciu)
        self.after(900, dalej)

    def po_otwarciu(self):
        self.scena.faza = "otwarty"
        self.scena.rysuj()
        o = self.d["obiekty"][self.obiekt]
        if not o.get("auto", True):
            self.scena.faza = "otwarty_staly"
            self.scena.rysuj()
            return

        def zamknij():
            self.scena.faza = "zamykanie"
            self.log("autozamykanie")
            self._ruch(1.0, self.wroc)
        self.after(max(1000, int(o.get("czas", 8) * 300)), zamknij)

    def wroc(self):
        self.scena.faza = "spoczynek"
        self.scena.kto = self.scena.tel = self.scena.powod = ""
        self.scena.rysuj()

    def recznie(self, otwierac):
        if self.scena.zablokowana:
            self.log("odrzucono — zapora zablokowana")
            return
        self.scena.faza = "otwieranie" if otwierac else "zamykanie"
        self.log("ręcznie: " + ("otwarcie na stałe" if otwierac else "zamknięcie"))
        self.zapisz_wjazd(None, "ręczne " + ("otwarcie" if otwierac else "zamknięcie"))
        self._ruch(0.0 if otwierac else 1.0,
                   lambda: self._po_recznym(otwierac))

    def _po_recznym(self, otwierac):
        self.scena.faza = "otwarty_staly" if otwierac else "spoczynek"
        self.scena.rysuj()

    def blokada(self):
        self.scena.zablokowana = not self.scena.zablokowana
        if self.scena.zablokowana:
            self.log("BLOKADA — połączenia ignorowane")
            if self.scena.postep < 1:
                self.scena.faza = "zamykanie"
                self._ruch(1.0, lambda: self._ustaw_faze("blokada"))
            else:
                self._ustaw_faze("blokada")
        else:
            self.log("blokada zdjęta")
            self._ustaw_faze("spoczynek")

    def _ustaw_faze(self, faza):
        self.scena.faza = faza
        self.scena.rysuj()

    def zapisz_wjazd(self, k, sposob):
        o = self.d["obiekty"][self.obiekt]
        teraz = datetime.now()
        self.d.setdefault("historia", []).append({
            "data": teraz.strftime("%d.%m.%Y"),
            "godzina": teraz.strftime("%H:%M"),
            "imie": k["imie"] if k else "Obsługa",
            "tel": k["tel"] if k else "—",
            "obiekt": o["nazwa"] + " — " + o["miejsce"],
            "sposob": sposob})
        if k and not sposob.startswith("ODMOWA"):
            k["ile"] = k.get("ile", 0) + 1
        self.d["historia"] = self.d["historia"][-5000:]
        zapisz(self.d)
        self.scena.dzis = sum(
            1 for w in self.d["historia"]
            if w.get("obiekt", "").startswith(o["nazwa"])
            and w.get("data") == teraz.strftime("%d.%m.%Y"))

    def _petla(self):
        # Przy zmianie motywu okno jest przebudowywane. Gdyby odliczanie
        # trafilo w te chwile, rysowanie dotyczyloby juz usunietego plotna.
        try:
            if self.widoki["podglad"].winfo_ismapped():
                if getattr(self, "scena_widoczna", False):
                    self.scena.rysuj()
                self.odswiez_kafle()
                self.odswiez_przeglad()
        except tk.TclError:
            pass
        self.after(1000, self._petla)

    # ---------------- narzedzia ----------------

    def _zastosuj_tlo(self):
        """Zapisuje i przemalowuje — wywolywane po zatrzymaniu suwaka."""
        self._zad_tlo = None
        zapisz(self.d)
        self.przemaluj_tla()
        self.log("przezroczystość tła: "
                 + str(self.d.get("przezroczystosc_tla", 46)) + "%")

    def zmien_styl(self, nr):
        """Przelacza palete barw i przebudowuje okno."""
        if self.d.get("styl", 3) == nr:
            return
        self.d["styl"] = nr
        self.d["motyw"] = "jasny" if STYLE[nr][1].get("welon") else "ciemny"
        zapisz(self.d)
        self.log("styl: " + STYLE[nr][0])
        self._przebuduj(styl=nr)

    def _przebuduj(self, styl=None):
        """Buduje okno od nowa w nowej palecie, zachowujac stan obiektow."""
        if self.animacja:
            self.after_cancel(self.animacja)
            self.animacja = None
        zastosuj_motyw(self.d.get("motyw") == "jasny", styl or self.d.get("styl"))
        stan = {o["id"]: dict(s) for o, s in
                zip(self.d["obiekty"], self.stany.values())}
        otwarty = getattr(self, "obiekt_otwarty", False)
        for w in self.winfo_children():
            w.destroy()
        self._tla = []
        self.configure(bg=B["tlo"])
        self._buduj()
        self.stany.update(stan)
        self.przelacz("ustawienia")
        if otwarty:
            self.otworz_obiekt(self.obiekt)

    def przelacz_motyw(self):
        if self.animacja:
            self.after_cancel(self.animacja)
            self.animacja = None
        jasny = self.d.get("motyw") != "jasny"
        self.d["motyw"] = "jasny" if jasny else "ciemny"
        zapisz(self.d)
        zastosuj_motyw(jasny)
        stan = {o["id"]: dict(s) for o, s in
                zip(self.d["obiekty"], self.stany.values())}
        for w in self.winfo_children():
            w.destroy()
        self.configure(bg=B["tlo"])
        self._buduj()
        self.stany.update(stan)
        self.b_motyw.configure(text="Tryb ciemny" if jasny else "Tryb jasny")

    def pelny_ekran(self):
        """Pelny ekran bez ramki i paska zadan — tryb dyzurki.
        Wyjscie klawiszem Escape albo tym samym przyciskiem."""
        wlaczony = getattr(self, "_pelny", False)
        self._pelny = not wlaczony
        self.attributes("-fullscreen", not wlaczony)
        self.d["pelny_ekran"] = not wlaczony
        zapisz(self.d)
        if not wlaczony:
            self.bind("<Escape>", lambda _e: self.pelny_ekran())
        else:
            self.unbind("<Escape>")
            self.otworz_na_caly_ekran()
        self.after(220, self.scena.rysuj)

    def zmien_nazwe(self):
        self.d["nazwa"] = self.pole_nazwa.get().strip() or NAZWA
        self.d["podtytul"] = self.pole_podtytul.get().strip()
        zapisz(self.d)
        self.title(f'{self.d["nazwa"]} — {self.d["podtytul"]}')
        self.lbl_wersja.configure(
            text=f'{self.d["nazwa"]} {wersja_programu()}  ·  Straż Akademicka')
        self.log("nazwa systemu: " + self.d["nazwa"])

    def wybierz_katalog(self):
        from tkinter import filedialog
        start = os.path.join(os.path.expanduser("~"), "OneDrive")
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        kat = filedialog.askdirectory(
            parent=self, initialdir=start,
            title="Wybierz katalog na bazę — najlepiej w OneDrive")
        if not kat:
            return
        stara = sciezka_bazy()
        if not ustaw_katalog_danych(kat):
            messagebox.showwarning("Katalog", "Nie udało się zapisać wskazania.",
                                   parent=self)
            return
        nowa = sciezka_bazy()
        if os.path.exists(stara) and not os.path.exists(nowa):
            try:
                import shutil
                shutil.copy2(stara, nowa)
                self.log("baza skopiowana do nowego katalogu")
            except OSError as e:
                self.log("nie udało się skopiować bazy: " + str(e))
        self.d = wczytaj()
        self.lbl_katalog.configure(text=katalog_danych())
        self.odswiez_kierowcow()
        messagebox.showinfo(
            "Katalog zmieniony",
            "Baza jest teraz w:\n" + katalog_danych() +
            "\n\nNa drugim komputerze zainstaluj program i wskaż ten sam "
            "katalog — numery pojawią się same.", parent=self)

    def katalog_domyslny_wroc(self):
        ustaw_katalog_danych("")
        self.d = wczytaj()
        self.lbl_katalog.configure(text=katalog_danych())
        self.odswiez_kierowcow()
        self.log("baza wróciła do katalogu domyślnego")

    def otworz_katalog(self):
        kat = katalog_danych()
        try:
            if sys.platform == "win32":
                os.startfile(kat)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", kat])
        except OSError as e:
            messagebox.showinfo("Katalog", kat, parent=self)
            self.log("nie udało się otworzyć katalogu: " + str(e))

    def kopia_zapisz(self):
        from tkinter import filedialog
        nazwa = "kopia-AWF-Kierowcy-" + datetime.now().strftime("%Y-%m-%d") + ".json"
        plik = filedialog.asksaveasfilename(
            parent=self, defaultextension=".json", initialfile=nazwa,
            filetypes=[("Kopia bazy", "*.json")], title="Zapisz kopię bazy")
        if not plik:
            return
        try:
            with open(plik, "w", encoding="utf-8") as f:
                json.dump(self.d, f, ensure_ascii=False, indent=1)
            self.log("zapisano kopię: " + os.path.basename(plik))
            messagebox.showinfo("Kopia", "Kopia zapisana.", parent=self)
        except OSError as e:
            messagebox.showwarning("Kopia", "Nie udało się zapisać:\n" + str(e),
                                   parent=self)

    def kopia_wczytaj(self):
        from tkinter import filedialog
        plik = filedialog.askopenfilename(
            parent=self, filetypes=[("Kopia bazy", "*.json")],
            title="Wczytaj kopię bazy")
        if not plik:
            return
        if not messagebox.askyesno(
                "Wczytanie kopii",
                "Obecna baza zostanie zastąpiona zawartością kopii.\n\n"
                "Kontynuować?", parent=self):
            return
        try:
            with open(plik, encoding="utf-8") as f:
                nowa = json.load(f)
            if "kierowcy" not in nowa:
                raise ValueError("to nie jest kopia bazy AWF KIEROWCY")
            self.d = nowa
            zapisz(self.d)
            self.odswiez_kierowcow()
            self.odswiez_historie()
            self.log("wczytano kopię: " + os.path.basename(plik))
            messagebox.showinfo(
                "Kopia", f'Wczytano {len(nowa.get("kierowcy", []))} numerów.',
                parent=self)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            messagebox.showwarning("Kopia", "Nie udało się wczytać:\n" + str(e),
                                   parent=self)

    def zmien_pin(self):
        from tkinter import simpledialog
        nowy = simpledialog.askstring("Zmiana PIN-u", "Nowy PIN (4–8 cyfr):",
                                      parent=self, show="●")
        if not nowy:
            return
        if not nowy.isdigit() or not 4 <= len(nowy) <= 8:
            messagebox.showwarning("PIN", "PIN musi mieć od 4 do 8 cyfr.",
                                   parent=self)
            return
        self.d["pin"] = zakoduj_pin(nowy)
        zapisz(self.d)
        # Ekran logowania przestaje pokazywac podpowiedz z fabrycznym PIN-em.
        ekran = getattr(self, "ekran_pin", None)
        try:
            if ekran is not None and ekran.winfo_exists():
                ekran.pin_fabryczny = (nowy == "1234")
        except tk.TclError:
            pass
        messagebox.showinfo("PIN", "PIN zmieniony.", parent=self)
        self.log("zmieniono PIN")

    def okno_kierowcy(self, idx):
        """Okno dodawania i edycji. idx=None znaczy nowy wpis."""
        nowy = idx is None or idx >= len(self.d["kierowcy"])
        k = ({"imie": "", "rola": "", "tel": "", "dni": list(DNI),
              "od": "00:00", "do": "23:59", "wazny": "", "ile": 0,
              "aktywny": True} if nowy else dict(self.d["kierowcy"][idx]))

        w = tk.Toplevel(self)
        w.title("Nowy numer" if nowy else "Edycja numeru")
        w.configure(bg=B["tlo2"])
        w.resizable(False, False)
        w.transient(self)
        w.grab_set()
        r = tk.Frame(w, bg=B["tlo2"], padx=26, pady=22)
        r.pack(fill="both", expand=True)

        def etykieta(tekst):
            tk.Label(r, text=tekst, bg=B["tlo2"], fg=B["przygasz"],
                     font=("Segoe UI", 9), anchor="w").pack(anchor="w",
                                                            pady=(12, 3))

        def pole(wartosc, szerokosc=42):
            e = tk.Entry(r, bg=B["tlo3"], fg=B["tekst"], relief="flat",
                         font=("Segoe UI", 11), insertbackground=B["tekst"],
                         width=szerokosc)
            e.insert(0, wartosc)
            e.pack(anchor="w", ipady=6, fill="x")
            return e

        etykieta("Kierowca lub nazwa firmy")
        p_imie = pole(k["imie"])
        etykieta("Rola")
        p_rola = ttk.Combobox(r, values=[
            "Straż Akademicka", "Rektorat", "Wydział", "Administracja",
            "Dział Techniczny", "Dostawca", "Wykonawca", "Serwis",
            "Pracownik", "Gość"], font=("Segoe UI", 11))
        p_rola.set(k.get("rola", ""))
        p_rola.pack(anchor="w", fill="x", ipady=3)
        etykieta("Numer telefonu")
        p_tel = pole(k["tel"])

        etykieta("Dni tygodnia")
        ram_dni = tk.Frame(r, bg=B["tlo2"])
        ram_dni.pack(anchor="w")
        zmienne = {}
        for i, (skrot, pelna) in enumerate(zip(DNI, DNI_PELNE)):
            v = tk.BooleanVar(value=skrot in k.get("dni", DNI))
            zmienne[skrot] = v
            tk.Checkbutton(ram_dni, text=skrot, variable=v, bg=B["tlo2"],
                           fg=B["tekst"], selectcolor=B["tlo3"],
                           activebackground=B["tlo2"], activeforeground=B["tekst"],
                           font=("Segoe UI", 10)).grid(row=0, column=i, padx=(0, 6))

        szybkie = tk.Frame(r, bg=B["tlo2"])
        szybkie.pack(anchor="w", pady=(6, 0))

        def ustaw_dni(lista):
            for sk, v in zmienne.items():
                v.set(sk in lista)
        for tekst, lista in (("cały tydzień", DNI), ("pn–pt", DNI[:5]),
                             ("weekend", DNI[5:])):
            tk.Button(szybkie, text=tekst, command=lambda l=lista: ustaw_dni(l),
                      relief="flat", bd=0, cursor="hand2", bg=B["tlo3"],
                      fg=B["tekst2"], font=("Segoe UI", 9), padx=10, pady=4
                      ).pack(side="left", padx=(0, 6))

        godz = tk.Frame(r, bg=B["tlo2"])
        godz.pack(anchor="w", fill="x", pady=(12, 0))
        for tekst, kol in (("Od godziny", 0), ("Do godziny", 1),
                           ("Ważny do (RRRR-MM-DD)", 2)):
            tk.Label(godz, text=tekst, bg=B["tlo2"], fg=B["przygasz"],
                     font=("Segoe UI", 9)).grid(row=0, column=kol, sticky="w",
                                                padx=(0, 10), pady=(0, 3))
        p_od = tk.Entry(godz, bg=B["tlo3"], fg=B["tekst"], relief="flat",
                        font=("Segoe UI", 11), width=9,
                        insertbackground=B["tekst"])
        p_od.insert(0, k.get("od", "00:00"))
        p_od.grid(row=1, column=0, sticky="w", ipady=6, padx=(0, 10))
        p_do = tk.Entry(godz, bg=B["tlo3"], fg=B["tekst"], relief="flat",
                        font=("Segoe UI", 11), width=9,
                        insertbackground=B["tekst"])
        p_do.insert(0, k.get("do", "23:59"))
        p_do.grid(row=1, column=1, sticky="w", ipady=6, padx=(0, 10))
        p_waz = tk.Entry(godz, bg=B["tlo3"], fg=B["tekst"], relief="flat",
                         font=("Segoe UI", 11), width=16,
                         insertbackground=B["tekst"])
        p_waz.insert(0, k.get("wazny", ""))
        p_waz.grid(row=1, column=2, sticky="w", ipady=6)

        v_akt = tk.BooleanVar(value=k.get("aktywny", True))
        tk.Checkbutton(r, text="Numer aktywny — może wjeżdżać",
                       variable=v_akt, bg=B["tlo2"], fg=B["tekst"],
                       selectcolor=B["tlo3"], activebackground=B["tlo2"],
                       activeforeground=B["tekst"], font=("Segoe UI", 10)
                       ).pack(anchor="w", pady=(16, 0))

        blad = tk.Label(r, text="", bg=B["tlo2"], fg=B["alarm"],
                        font=("Segoe UI", 9))
        blad.pack(anchor="w", pady=(8, 0))

        def zapisz_wpis():
            imie = p_imie.get().strip()
            tel = p_tel.get().strip()
            if not imie:
                blad.configure(text="Podaj kierowcę lub nazwę firmy.")
                return
            if not tel:
                blad.configure(text="Podaj numer telefonu.")
                return
            cyfry = "".join(z for z in tel if z.isdigit())
            if len(cyfry) < 9:
                blad.configure(text="Numer wygląda na za krótki.")
                return
            if len(cyfry) == 9:
                tel = "+48 " + cyfry[:3] + " " + cyfry[3:6] + " " + cyfry[6:]
            dni = [sk for sk, v in zmienne.items() if v.get()]
            if not dni:
                blad.configure(text="Zaznacz przynajmniej jeden dzień.")
                return
            for pole_g, nazwa in ((p_od, "Od"), (p_do, "Do")):
                t = pole_g.get().strip()
                try:
                    datetime.strptime(t, "%H:%M")
                except ValueError:
                    blad.configure(text=f"Godzina „{nazwa}” ma być w formacie 08:00.")
                    return
            waz = p_waz.get().strip()
            if waz:
                try:
                    datetime.strptime(waz, "%Y-%m-%d")
                except ValueError:
                    blad.configure(text="Data ważności ma być w formacie 2026-12-31.")
                    return

            wpis = {"imie": imie, "rola": p_rola.get().strip(), "tel": tel,
                    "dni": dni, "od": p_od.get().strip(),
                    "do": p_do.get().strip(), "wazny": waz,
                    "aktywny": v_akt.get(),
                    "ile": 0 if nowy else self.d["kierowcy"][idx].get("ile", 0)}
            if nowy:
                self.d["kierowcy"].append(wpis)
                self.log("dodano numer: " + imie)
            else:
                self.d["kierowcy"][idx] = wpis
                self.log("zapisano zmiany: " + imie)
            zapisz(self.d)
            self.odswiez_kierowcow()
            w.destroy()

        guziki = tk.Frame(r, bg=B["tlo2"])
        guziki.pack(fill="x", pady=(18, 0))
        tk.Button(guziki, text="Zapisz", command=zapisz_wpis, relief="flat",
                  bd=0, cursor="hand2", bg=B["akcent"], fg=B["naAkcencie"],
                  font=("Segoe UI Semibold", 10), padx=20, pady=9
                  ).pack(side="right")
        tk.Button(guziki, text="Anuluj", command=w.destroy, relief="flat",
                  bd=0, cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                  font=("Segoe UI", 10), padx=18, pady=9
                  ).pack(side="right", padx=(0, 8))

        p_imie.focus_set()
        w.bind("<Return>", lambda _e: zapisz_wpis())
        w.bind("<Escape>", lambda _e: w.destroy())
        w.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - w.winfo_width()) // 2
        y = self.winfo_rooty() + 70
        w.geometry(f"+{max(0, x)}+{max(0, y)}")

    def usun_kierowce(self):
        if not self.d["kierowcy"]:
            return
        k = self.d["kierowcy"][self.wybrany]
        if messagebox.askyesno("Usuwanie",
                               f'Usunąć numer: {k["imie"]}?', parent=self):
            self.d["kierowcy"].pop(self.wybrany)
            self.wybrany = max(0, self.wybrany - 1)
            zapisz(self.d)
            self.odswiez_kierowcow()
            self.log("usunięto numer: " + k["imie"])

    def raport(self):
        """Zestawienie w przegladarce — stamtad mozna wydrukowac
        albo zapisac jako PDF."""
        h = self.d.get("historia", [])
        if not h:
            messagebox.showinfo("Raport", "Historia jest pusta.", parent=self)
            return

        teraz = datetime.now()
        dzis = teraz.strftime("%d.%m.%Y")
        odmowy = [w for w in h if w.get("sposob", "").startswith("ODMOWA")]
        reczne = [w for w in h if "ręczne" in w.get("sposob", "")]

        godziny = {}
        for w in h:
            g = w.get("godzina", "")[:2]
            if g.isdigit():
                godziny[g] = godziny.get(g, 0) + 1
        szczyt = max(godziny.items(), key=lambda x: x[1])[0] if godziny else "—"

        osoby = {}
        for w in h:
            if not w.get("sposob", "").startswith("ODMOWA"):
                osoby[w.get("imie", "?")] = osoby.get(w.get("imie", "?"), 0) + 1
        naj = sorted(osoby.items(), key=lambda x: -x[1])[:10]

        obiekty = {}
        for w in h:
            obiekty[w.get("obiekt", "?")] = obiekty.get(w.get("obiekt", "?"), 0) + 1

        def wiersze(lista):
            out = []
            for w in lista:
                sposob = w.get("sposob", "")
                klasa = ("odmowa" if sposob.startswith("ODMOWA")
                         else ("reczne" if "ręczne" in sposob else ""))
                out.append(
                    f'<tr class="{klasa}"><td>{w.get("data","")}</td>'
                    f'<td>{w.get("godzina","")}</td><td>{w.get("imie","")}</td>'
                    f'<td>{w.get("tel","")}</td><td>{w.get("obiekt","")}</td>'
                    f'<td>{sposob}</td></tr>')
            return "\n".join(out)

        html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<title>Raport wjazdów — {dzis}</title><style>
body{{font:12pt "Segoe UI",sans-serif;color:#111;margin:26px;}}
h1{{font-size:19pt;margin:0;color:#006341}}
.pod{{color:#666;font-size:10pt;margin:3px 0 22px}}
.kafle{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px}}
.k{{border:1px solid #cddbd2;padding:11px 16px;min-width:120px}}
.k .e{{font-size:8pt;color:#777;text-transform:uppercase;letter-spacing:.5px}}
.k .w{{font-size:19pt;font-weight:600;color:#006341;margin-top:3px}}
table{{width:100%;border-collapse:collapse;font-size:9.5pt}}
th{{background:#006341;color:#fff;text-align:left;padding:7px 9px;font-size:8pt;
    text-transform:uppercase}}
td{{padding:6px 9px;border-bottom:1px solid #e4ebe6}}
tr.odmowa td{{color:#b32626}}
tr.reczne td{{color:#8a6a2e}}
h2{{font-size:12pt;margin:26px 0 8px;color:#006341}}
.stopka{{margin-top:26px;padding-top:10px;border-top:1px solid #cddbd2;
        font-size:8.5pt;color:#777}}
@media print{{body{{margin:12mm}} .k{{break-inside:avoid}}}}
</style></head><body>

<h1>Raport wjazdów</h1>
<div class="pod">{self.d.get("nazwa", NAZWA)} · Straż Akademicka AWF ·
sporządzono {teraz.strftime("%d.%m.%Y o %H:%M")}</div>

<div class="kafle">
  <div class="k"><div class="e">Wszystkich wpisów</div><div class="w">{len(h)}</div></div>
  <div class="k"><div class="e">Dzisiaj</div><div class="w">{sum(1 for w in h if w.get("data") == dzis)}</div></div>
  <div class="k"><div class="e">Odmowy</div><div class="w">{len(odmowy)}</div></div>
  <div class="k"><div class="e">Ręczne otwarcia</div><div class="w">{len(reczne)}</div></div>
  <div class="k"><div class="e">Szczyt ruchu</div><div class="w">{szczyt}:00</div></div>
</div>

<h2>Obiekty</h2>
<table><tr><th>Obiekt</th><th>Wjazdów</th></tr>
{"".join(f"<tr><td>{o}</td><td>{n}</td></tr>" for o, n in sorted(obiekty.items(), key=lambda x: -x[1]))}
</table>

<h2>Najczęściej wjeżdżający</h2>
<table><tr><th>Kierowca</th><th>Wjazdów</th></tr>
{"".join(f"<tr><td>{i}</td><td>{n}</td></tr>" for i, n in naj)}
</table>

<h2>Odmowy dostępu ({len(odmowy)})</h2>
<table><tr><th>Data</th><th>Godzina</th><th>Kierowca</th><th>Telefon</th>
<th>Obiekt</th><th>Powód</th></tr>
{wiersze(odmowy[-40:]) if odmowy else '<tr><td colspan="6">brak</td></tr>'}
</table>

<h2>Ostatnie wjazdy</h2>
<table><tr><th>Data</th><th>Godzina</th><th>Kierowca</th><th>Telefon</th>
<th>Obiekt</th><th>Sposób</th></tr>
{wiersze(list(reversed(h))[:120])}
</table>

<div class="stopka">
Akademia Wychowania Fizycznego Józefa Piłsudskiego w Warszawie ·
Marymoncka 34, 00-968 Warszawa · straz@awf.edu.pl<br>
Dokument zawiera dane osobowe — przechowywać zgodnie z zasadami uczelni.
</div>
</body></html>"""

        try:
            import tempfile
            import webbrowser
            plik = os.path.join(tempfile.gettempdir(),
                                f"raport-wjazdow-{teraz.strftime('%Y%m%d-%H%M')}.html")
            with open(plik, "w", encoding="utf-8") as f:
                f.write(html)
            webbrowser.open("file://" + plik.replace("\\", "/"))
            self.log("raport otwarty w przeglądarce")
        except OSError as e:
            messagebox.showwarning("Raport", "Nie udało się utworzyć raportu:\n"
                                   + str(e), parent=self)

    def czysc_historie(self):
        granica = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        def klucz(w):
            try:
                d, m, r = w.get("data", "01.01.1970").split(".")
                return r + m + d
            except ValueError:
                return "99999999"
        przed = len(self.d.get("historia", []))
        self.d["historia"] = [w for w in self.d.get("historia", [])
                              if klucz(w) >= granica]
        zapisz(self.d)
        self.odswiez_historie()
        self.log(f"usunięto {przed - len(self.d['historia'])} starych wpisów")

    # ---------------- aktualizacje ----------------

    # ------- cicha aktualizacja przed zalogowaniem -------

    def tryb_aktualizacji(self):
        """'pyta' (domyslnie), 'sam' albo 'wylaczone'.

        Domyslnie program pyta — o zamknieciu i podmianie plikow decyduje
        dyzurny. Wgrywanie bez pytania trzeba wlaczyc recznie.
        """
        tryb = self.d.get("tryb_aktualizacji")
        if tryb in ("pyta", "sam", "wylaczone"):
            return tryb
        if self.d.get("sprawdzaj_aktualizacje") is False:
            return "wylaczone"
        return "pyta"

    def _cicha_aktualizacja(self):
        """Sprawdza serwer i sam wgrywa nowa wersje, zanim ktos wpisze PIN.

        Na ekranie logowania nikt nie pracuje, wiec zamkniecie i ponowne
        uruchomienie niczego nie przerywa. Po rozpoczeciu pobierania
        klawiatura jest zablokowana az do konca — inaczej dyzurny zalogowalby
        sie w chwili, gdy program ma sie zamknac.
        """
        try:
            import aktualizacje                      # noqa: F401
        except ImportError:
            return
        if self.tryb_aktualizacji() == "wylaczone":
            self._napis_pin("v" + wersja_programu())
            return
        import queue
        import threading
        self._kolejka_cicha = queue.Queue()

        def robota():
            import aktualizacje
            self._kolejka_cicha.put(aktualizacje.stan_serwera(VER))

        threading.Thread(target=robota, daemon=True).start()
        self._odbierz_cicha()

    def _odbierz_cicha(self):
        import queue
        try:
            rodzaj, dane = self._kolejka_cicha.get_nowait()
        except queue.Empty:
            self.after(250, self._odbierz_cicha)
            return
        self._akt_stan = rodzaj
        if rodzaj == "jest":
            # Domyslnie pytamy — o zamknieciu programu decyduje dyzurny.
            # Wgrywanie bez pytania dziala tylko wtedy, gdy ktos wlaczyl je
            # recznie w Ustawieniach.
            if self.tryb_aktualizacji() == "sam":
                self._wgraj_po_cichu(dane)
            elif self._zalogowany:
                self._pytaj_po_zalogowaniu(dane)
            else:
                self._zapytaj_o_aktualizacje(dane)
        elif rodzaj == "aktualna":
            self._napis_pin("v" + wersja_programu() + " — najnowsza")
        else:
            self._napis_pin("v" + wersja_programu())

    def _pytaj_po_zalogowaniu(self, info):
        """Pytanie o aktualizacje w oknie programu, po zalogowaniu.

        Dyzurny widzi juz panel i wie, co sie dzieje na obiektach — dopiero
        wtedy decyduje, czy zamknac program na czas podmiany plikow.
        """
        opis = (info.get("opis") or "").strip()
        tresc = f"Dostępna jest wersja {info['wersja']}.\n\n"
        if opis:
            tresc += opis.split("\n\n", 1)[-1][:280] + "\n\n"
        tresc += ("Wgranie potrwa kilkadziesiąt sekund. Program zamknie się "
                  "i uruchomi ponownie — przez ten czas zapora i szlabany "
                  "nie będą obsługiwane z tego komputera.")
        if okno_pytania(self, "Nowa wersja programu", tresc,
                        tak="Wgraj teraz", nie="Nie teraz"):
            self._wgraj_po_cichu(info)
        else:
            self._pasek_informacyjny(
                f"Wersja {info['wersja']} czeka — możesz ją wgrać "
                "w Ustawieniach", B["uwaga"])

    def _zapytaj_o_aktualizacje(self, info):
        """Pyta raz, przed wpisaniem PIN-u. Zgoda zostaje zapamietana
        i od nastepnego razu program wgrywa aktualizacje bez pytania."""
        ekran = getattr(self, "ekran_pin", None)
        if ekran is None or not ekran.winfo_exists():
            return

        def tak():
            # Zgody nie zapisujemy. Program ma pytac za kazdym razem —
            # wgrywanie bez pytania wlacza sie recznie w Ustawieniach.
            self._wgraj_po_cichu(info)

        def nie():
            # nic nie zapisujemy — przy nastepnym uruchomieniu spytamy znowu
            self._napis_pin(f"dostępna {info['wersja']}", B["zloto"])

        ekran.zapytaj_o_aktualizacje(info["wersja"], tak, nie)

    def _napis_pin(self, tekst, kolor=None):
        ekran = getattr(self, "ekran_pin", None)
        try:
            if ekran is not None and ekran.winfo_exists():
                ekran.komunikat(tekst, kolor)
        except tk.TclError:
            pass

    def _pasek_pin(self, ulamek, tekst=""):
        ekran = getattr(self, "ekran_pin", None)
        try:
            if ekran is not None and ekran.winfo_exists():
                ekran.postep(ulamek, tekst)
        except tk.TclError:
            pass

    def _schowaj_pasek_pin(self):
        ekran = getattr(self, "ekran_pin", None)
        try:
            if ekran is not None and ekran.winfo_exists():
                ekran.schowaj_postep()
        except tk.TclError:
            pass

    def _wgraj_po_cichu(self, info):
        import queue
        import threading
        self._kolejka_wgrania = queue.Queue()
        if self._zalogowany:
            self._pasek_informacyjny(
                f"Pobieram wersję {info['wersja']}...", B["uwaga"],
                trwaly=True)
        else:
            self._pasek_pin(0.0, f"Aktualizacja do {info['wersja']}")
            self._napis_pin(f"v{wersja_programu()} \u2192 {info['wersja']}",
                            B["zloto"])
        self.log(f'dostępna wersja {info["wersja"]} — wgrywam sama')

        def robota():
            import aktualizacje
            try:
                plik = aktualizacje.pobierz(
                    info,
                    postep=lambda u: self._kolejka_wgrania.put(("postep", u)))
                self._kolejka_wgrania.put(("etap", "Rozpakowywanie"))
                nowe = aktualizacje.rozpakuj(plik)
                bat = aktualizacje.przygotuj_pomocnika(
                    nowe, aktualizacje.katalog_programu(),
                    wersja=info.get("wersja", ""))
                self._kolejka_wgrania.put(("gotowe", bat))
            except Exception as blad:                # noqa: BLE001
                self._kolejka_wgrania.put(("blad", str(blad)))

        threading.Thread(target=robota, daemon=True).start()
        self._odbierz_wgranie(info)

    def _odbierz_wgranie(self, info):
        import queue
        try:
            rodzaj, tresc = self._kolejka_wgrania.get_nowait()
        except queue.Empty:
            self.after(200, lambda: self._odbierz_wgranie(info))
            return

        if rodzaj == "postep":
            if self._zalogowany:
                self._pasek_informacyjny(
                    f"Pobieram wersję {info['wersja']} — "
                    f"{round(tresc * 100)}%", B["uwaga"], trwaly=True)
            else:
                self._pasek_pin(tresc, f"Aktualizacja do {info['wersja']}")
            self.after(100, lambda: self._odbierz_wgranie(info))
            return

        if rodzaj == "etap":
            self._pasek_pin(1.0, tresc)
            self.after(100, lambda: self._odbierz_wgranie(info))
            return

        if rodzaj == "blad":
            # Nieudane pobranie nie moze przeszkodzic w zalogowaniu —
            # odblokowujemy klawiature i zostajemy na starej wersji.
            self._schowaj_pasek_pin()
            self._napis_pin("v" + wersja_programu())
            self.log("cicha aktualizacja nieudana: " + str(tresc))
            return

        if self._zalogowany:
            # Ktos wpisal PIN w trakcie pobierania. Nie zamykamy programu
            # w czasie sluzby — pytamy, kiedy ma sie przelaczyc.
            self._czeka_pomocnik = tresc
            self.log(f'wersja {info["wersja"]} pobrana — czeka na ponowne '
                     'uruchomienie')
            self.after(800, lambda: self._pytaj_o_restart(info["wersja"]))
            return

        self._pasek_pin(1.0, "Zamykam się — zaraz wrócę")
        self.update_idletasks()
        import aktualizacje
        aktualizacje.uruchom_pomocnika(tresc)
        self._zamykam_sam = True
        self.after(400, self.destroy)

    def _pytaj_o_restart(self, wersja):
        """Nowa wersja jest pobrana, ale program dziala. Pytamy, czy
        przelaczyc teraz — sam z siebie nie zamknie sie w czasie sluzby."""
        if okno_pytania(
                self, "Aktualizacja gotowa",
                f"Wersja {wersja} została pobrana.\n\n"
                "Uruchomić program ponownie teraz, żeby ją włączyć? "
                "Potrwa to kilka sekund.",
                tak="Uruchom ponownie", nie="Później"):
            import aktualizacje
            aktualizacje.uruchom_pomocnika(self._czeka_pomocnik)
            self._zamykam_sam = True
            self.after(400, self.destroy)
        else:
            self._pasek_informacyjny(
                f"Wersja {wersja} czeka — włączy się przy następnym "
                "uruchomieniu", B["akcent"])

    def _pokaz_wynik_aktualizacji(self):
        """Po aktualizacji program wraca sam. Tu melduje, jak poszlo —
        okno pomocnika jest ukryte, wiec to jedyna informacja zwrotna."""
        try:
            import aktualizacje
        except ImportError:
            return
        wynik = aktualizacje.odczytaj_wynik()
        if not wynik:
            return
        rodzaj, tresc = wynik
        if rodzaj == "OK":
            self.log(f"zaktualizowano do wersji {tresc or wersja_programu()}")
            nowa = tresc or wersja_programu()
            self.after(600, lambda: self._pasek_informacyjny(
                f"Zaktualizowano do wersji {nowa}", B["ok"]))
        else:
            self.log("aktualizacja nieudana: " + tresc)
            self.after(600, lambda: messagebox.showwarning(
                "Aktualizacja", tresc + "\n\nProgram działa w poprzedniej "
                "wersji.", parent=self))

    def _pasek_informacyjny(self, tekst, kolor, trwaly=False):
        """Waski pasek u gory okna.

        JEDEN pasek, nie nowy przy kazdym wywolaniu. Wczesniej kazde
        wywolanie tworzylo kolejna ramke — przy pobieraniu aktualizacji,
        gdzie tekst zmienia sie co procent, zasypywalo to caly ekran.
        Teraz przy kolejnym wywolaniu podmieniamy tylko napis.

        trwaly=True — pasek nie znika sam (uzywane przy pobieraniu).
        """
        istnieje = getattr(self, "_pasek_inf", None)
        try:
            zyje = istnieje is not None and istnieje.winfo_exists()
        except tk.TclError:
            zyje = False

        if zyje:
            istnieje.configure(bg=kolor)
            self._pasek_inf_txt.configure(text=tekst, bg=kolor)
            self._pasek_inf_x.configure(bg=kolor)
        else:
            pasek = tk.Frame(self, bg=kolor, height=34)
            pasek.pack(fill="x", before=self.tresc)
            pasek.pack_propagate(False)
            self._pasek_inf = pasek
            self._pasek_inf_txt = tk.Label(
                pasek, text=tekst, bg=kolor, fg=B["naAkcencie"],
                font=("Segoe UI Semibold", 10))
            self._pasek_inf_txt.pack(side="left", padx=18)
            self._pasek_inf_x = tk.Label(
                pasek, text="✕", bg=kolor, fg=B["naAkcencie"],
                font=("Segoe UI", 11), cursor="hand2", padx=16)
            self._pasek_inf_x.pack(side="right")
            for dziecko in (pasek, self._pasek_inf_txt, self._pasek_inf_x):
                dziecko.bind("<Button-1>", lambda _e: self._zamknij_pasek())

        # kazde wywolanie kasuje poprzednie odliczanie — inaczej pasek
        # znikalby w trakcie pobierania
        if getattr(self, "_zad_pasek", None):
            try:
                self.after_cancel(self._zad_pasek)
            except (ValueError, tk.TclError):
                pass
            self._zad_pasek = None
        if not trwaly:
            self._zad_pasek = self.after(8000, self._zamknij_pasek)

    def _zamknij_pasek(self):
        self._zad_pasek = None
        pasek = getattr(self, "_pasek_inf", None)
        try:
            if pasek is not None and pasek.winfo_exists():
                pasek.destroy()
        except tk.TclError:
            pass
        self._pasek_inf = None

    def _sprawdz_aktualizacje(self):
        """Sprawdzenie przy starcie — po cichu. Gdy nie ma nowszej wersji
        albo nie ma internetu, nic sie nie dzieje."""
        try:
            import aktualizacje
        except ImportError:
            return
        import queue
        import threading
        self._kolejka_start = queue.Queue()

        def robota():
            self._kolejka_start.put(aktualizacje.stan_serwera(VER))

        threading.Thread(target=robota, daemon=True).start()
        self._odbierz_start()

    def _odbierz_start(self):
        import queue
        try:
            rodzaj, dane = self._kolejka_start.get_nowait()
        except queue.Empty:
            self.after(200, self._odbierz_start)
            return
        if rodzaj == "jest":
            self._jest_aktualizacja(dane)
        elif rodzaj == "aktualna":
            self.log(f"wersja {wersja_programu()} — najnowsza")
        else:
            self.log("nie sprawdzono aktualizacji: " + str(dane))

    def _jest_aktualizacja(self, info):
        self.log(f'dostępna wersja {info["wersja"]}')
        try:
            from okno_aktualizacji import okno_aktualizacji
            okno_aktualizacji(self, info)
        except ImportError:
            messagebox.showinfo(
                "Aktualizacja",
                f'Dostępna wersja {info["wersja"]}\n\n{info.get("opis","")}',
                parent=self)

    def okno_historii(self):
        """Lista wydan z opisem zmian — pobierana z GitHuba."""
        w = tk.Toplevel(self)
        w.title("Co nowego w kolejnych wersjach")
        w.configure(bg=B["tlo"])
        w.geometry("640x560")
        w.transient(self)

        gora = tk.Frame(w, bg=B["tlo2"], height=56)
        gora.pack(fill="x")
        gora.pack_propagate(False)
        tk.Label(gora, text="Historia wersji", bg=B["tlo2"], fg=B["tekst"],
                 font=("Segoe UI Semibold", 13)).pack(side="left", padx=18)
        tk.Label(gora, text="masz " + wersja_programu(), bg=B["tlo2"], fg=B["zloto"],
                 font=("Segoe UI Semibold", 10)).pack(side="right", padx=18)

        pole = tk.Text(w, bg=B["tlo"], fg=B["tekst"], relief="flat",
                       font=("Segoe UI", 10), padx=20, pady=16, wrap="word",
                       spacing1=2, spacing3=4)
        pas = ttk.Scrollbar(w, orient="vertical", command=pole.yview)
        pole.configure(yscrollcommand=pas.set)
        pas.pack(side="right", fill="y")
        pole.pack(fill="both", expand=True)

        pole.tag_configure("wersja", font=("Segoe UI Semibold", 13),
                           foreground=B["akcent"], spacing1=14, spacing3=2)
        pole.tag_configure("biezaca", font=("Segoe UI Semibold", 13),
                           foreground=B["zloto"], spacing1=14, spacing3=2)
        pole.tag_configure("data", font=("Consolas", 9), foreground=B["przygasz"])
        pole.tag_configure("punkt", lmargin1=14, lmargin2=26)
        pole.tag_configure("info", foreground=B["przygasz"],
                           font=("Segoe UI", 10))

        pole.insert("end", "Pobieranie...\n", "info")
        pole.configure(state="disabled")

        import queue
        import threading
        kolejka = queue.Queue()

        def robota():
            try:
                import aktualizacje
                kolejka.put(aktualizacje.historia_wersji())
            except ImportError:
                kolejka.put([])

        def odbierz():
            try:
                lista = kolejka.get_nowait()
            except queue.Empty:
                w.after(150, odbierz)
                return
            pole.configure(state="normal")
            pole.delete("1.0", "end")
            if not lista:
                pole.insert("end",
                            "Nie udało się pobrać historii wersji.\n\n"
                            "Sprawdź połączenie z internetem albo zajrzyj na\n"
                            "github.com/superdarco78/AWF-Kierowcy/releases\n",
                            "info")
            else:
                for wyd in lista:
                    biezaca = wyd["wersja"] == VER
                    naglowek = "Wersja " + wyd["wersja"]
                    if biezaca:
                        naglowek += "   ← ta, którą masz"
                    pole.insert("end", naglowek + "\n",
                                "biezaca" if biezaca else "wersja")
                    if wyd["data"]:
                        pole.insert("end", wyd["data"] + "\n", "data")
                    for linia in wyd["opis"].splitlines():
                        linia = linia.strip()
                        if not linia or linia.lower().startswith("co nowego"):
                            continue
                        pole.insert("end", linia + "\n", "punkt")
            pole.configure(state="disabled")

        threading.Thread(target=robota, daemon=True).start()
        odbierz()

        tk.Button(w, text="Zamknij", command=w.destroy, relief="flat", bd=0,
                  cursor="hand2", bg=B["tlo3"], fg=B["tekst"],
                  font=("Segoe UI", 10), padx=18, pady=8).pack(pady=(0, 14))

        w.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - w.winfo_width()) // 2
        y = self.winfo_rooty() + 60
        w.geometry(f"+{max(0, x)}+{max(0, y)}")

    def sprawdz_recznie(self):
        try:
            import aktualizacje
        except ImportError:
            messagebox.showinfo("Aktualizacje",
                                "Brak modułu aktualizacji w katalogu programu.",
                                parent=self)
            return
        self.lbl_akt.configure(text="Sprawdzanie...", fg=B["przygasz"])
        self.log("sprawdzam aktualizacje na GitHubie")
        self.update_idletasks()

        # Watek roboczy nie dotyka okien — wklada wynik do kolejki,
        # a watek glowny co 150 ms zaglada, czy cos przyszlo.
        import queue
        import threading
        self._kolejka_akt = queue.Queue()

        def robota():
            self._kolejka_akt.put(aktualizacje.stan_serwera(VER))

        threading.Thread(target=robota, daemon=True).start()
        self._odbierz_sprawdzenie()

    def _odbierz_sprawdzenie(self):
        import queue
        try:
            rodzaj, dane = self._kolejka_akt.get_nowait()
        except queue.Empty:
            self.after(150, self._odbierz_sprawdzenie)
            return
        self._wynik_sprawdzenia(rodzaj, dane)

    def _wynik_sprawdzenia(self, rodzaj, dane):
        czas = datetime.now().strftime("%H:%M")
        if rodzaj == "jest":
            self.lbl_akt.configure(
                text=f"Masz {VER}, dostępna {dane['wersja']}", fg=B["uwaga"])
            self.log(f"dostępna wersja {dane['wersja']}")
            self._jest_aktualizacja(dane)
        elif rodzaj == "aktualna":
            self.lbl_akt.configure(
                text=f"Wersja {VER} — najnowsza  ·  sprawdzono {czas}",
                fg=B["ok"])
            self.log(f"masz najnowszą wersję ({dane})")
        else:
            self.lbl_akt.configure(
                text=f"Nie sprawdzono: {dane}  ·  {czas}", fg=B["alarm"])
            self.log("sprawdzanie nieudane: " + str(dane))


def _sprawdz_jedno_uruchomienie():
    """Drugie uruchomienie tylko melduje i konczy sie — bez okna programu."""
    if not juz_dziala():
        return
    korzen = tk.Tk()
    korzen.withdraw()
    messagebox.showinfo(
        NAZWA,
        "Program już działa.\n\n"
        "Poszukaj go na pasku zadań — okno jest otwarte.\n"
        "Dwie kopie naraz zapisywałyby tę samą bazę i jedna kasowałaby "
        "pracę drugiej.")
    korzen.destroy()
    sys.exit(0)


if __name__ == "__main__":
    _sprawdz_jedno_uruchomienie()
    App().mainloop()
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
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
except ImportError:
    print("Brakuje biblioteki Pillow. Uruchom: pip install pillow")
    sys.exit(1)

VER = "6.1"
NAZWA = "AWF KIEROWCY"
PODTYTUL = "Kontrola wjazdu i wyjazdu"

DNI = ["pn", "wt", "sr", "cz", "pt", "so", "nd"]
DNI_PELNE = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek",
             "sobota", "niedziela"]


# ==========================================================================
# barwy — dwa komplety, jak w bloku :root i body.jasny we wzorcu
# ==========================================================================

# Obie palety wyprowadzone z dwoch barw uczelni: zielen #036744 i zloto
# #b9975b. Tla to ta sama zielen zmieszana z czernia, napisy — z biela,
# wiec caly program trzyma sie jednej rodziny barw.
#
# Zielen uczelni jest ciemna, dlatego sluzy jako WYPELNIENIE z bialym
# napisem (kontrast 6,9). Jako napis na ciemnym tle bylaby nieczytelna
# (2,6), wiec do tego jest osobny klucz "akcentTekst" — ta sama zielen
# rozjasniona biela. Zloto odwrotnie: na ciemnym tle wlasne #b9975b,
# na bialym przyciemnione, bo jasne zloto na bieli ma kontrast 2,8.

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

B = dict(CIEMNY)          # biezaca paleta


def zastosuj_motyw(jasny):
    B.clear()
    B.update(JASNY if jasny else CIEMNY)


# ==========================================================================
# pliki i dane
# ==========================================================================

def zasob(nazwa):
    """Sciezka do pliku dolaczonego do programu.

    Szuka po kolei we wszystkich miejscach, w ktorych PyInstaller potrafi
    zostawic dolaczone pliki — inaczej po aktualizacji zdjecie tla potrafi
    zniknac tylko dlatego, ze wyladowalo w innym podkatalogu.
    """
    miejsca = []
    if hasattr(sys, "_MEIPASS"):
        miejsca.append(sys._MEIPASS)
    if getattr(sys, "frozen", False):
        obok = os.path.dirname(os.path.abspath(sys.executable))
        miejsca += [obok, os.path.join(obok, "_internal")]
    miejsca.append(os.path.dirname(os.path.abspath(__file__)))
    for m in miejsca:
        p = os.path.join(m, nazwa)
        if os.path.exists(p):
            return p
    return None


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
        kol = "#f2b544" if ruch else ("#37c76a" if self.postep < 0.1 else "#4a3a1c")
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
        return {
            "spoczynek": (("ZAPORA ZAMKNIĘTA" if self.typ == "slupki"
                           else "SZLABAN OPUSZCZONY"), B["zloto"]),
            "blokada": ("BLOKADA — POŁĄCZENIA IGNOROWANE", B["alarm"]),
            "dzwoni": ("POŁĄCZENIE PRZYCHODZĄCE", B["uwaga"]),
            "otwieranie": (("SŁUPKI OPADAJĄ" if self.typ == "slupki"
                            else "SZLABAN SIĘ PODNOSI"), B["ok"]),
            "otwarty": ("PRZEJAZD WOLNY", B["ok"]),
            "otwarty_staly": ("PRZEJAZD OTWARTY NA STAŁE", B["uwaga"]),
            "zamykanie": (("SŁUPKI PODNOSZĄ SIĘ" if self.typ == "slupki"
                           else "SZLABAN OPADA"), B["uwaga"]),
            "odmowa": ("DOSTĘP ZABLOKOWANY", B["alarm"]),
        }.get(self.faza, ("GOTOWA", B["tekst"]))

    def _hud(self, LP, W, H):
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
    """Ekran logowania: zdjecie w tle i klawiatura ze zwyklych przyciskow.

    Swiadomie bez skladania calego ekranu w obraz — zwykle przyciski
    dzialaja wszedzie, a zdjecie jest tylko tlem pod nimi.
    """

    KLAWISZE = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "C", "0", "OK"]

    def __init__(self, rodzic, sprawdz, po_zalogowaniu):
        super().__init__(rodzic, bg=B["tlo"])
        self.sprawdz = sprawdz
        self.po_zalogowaniu = po_zalogowaniu
        self.wpisany = ""
        self.proby = 0
        self._tlo_tk = None
        self._rozmiar = None

        self.tlo = tk.Label(self, bd=0, bg=B["tlo"])
        self.tlo.place(x=0, y=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._na_zmiane)

        self.karta = tk.Frame(self, bg=B["tlo2"], highlightthickness=1,
                              highlightbackground=B["zloto2"])
        self.karta.place(relx=0.5, rely=0.5, anchor="center")
        self._buduj_karte()

        # Numer wersji i stan aktualizacji — widoczne jeszcze przed PIN-em.
        # Dyzurny ma wiedziec, co ma zainstalowane, bez logowania sie.
        self.stopka = tk.Label(self, text="v" + VER, bg=B["tlo2"],
                               fg=B["zloto"], font=("Segoe UI", 9),
                               padx=10, pady=4)
        self.stopka.place(relx=0.99, rely=0.98, anchor="se")

        self.bind_all("<Key>", self._klawisz)

    # ---------------- tlo ----------------

    def _na_zmiane(self, _e=None):
        W, H = self.winfo_width(), self.winfo_height()
        if W < 50 or H < 50 or (W, H) == self._rozmiar:
            return
        self._rozmiar = (W, H)
        plik = zasob("logowanie-tlo.jpg")
        if not plik:
            # Zdjecia nie ma — mowimy o tym wprost, zamiast pokazywac
            # pusty ekran i zgadywac, czy to wina programu.
            self.tlo.configure(image="", bg=B["tlo"])
            self.komunikat("brak pliku logowanie-tlo.jpg", B["uwaga"])
            return
        try:
            obraz = Image.open(plik).convert("RGB")
            sk = max(W / obraz.width, H / obraz.height)
            nowy = obraz.resize((max(1, int(obraz.width * sk)),
                                 max(1, int(obraz.height * sk))),
                                Image.LANCZOS)
            lewy = (nowy.width - W) // 2
            gorny = int((nowy.height - H) * 0.45)
            kadr = nowy.crop((lewy, gorny, lewy + W, gorny + H))
            naklad = Image.new("RGBA", (W, H), (4, 14, 9, 96))
            kadr = Image.alpha_composite(kadr.convert("RGBA"), naklad)
            self._tlo_tk = ImageTk.PhotoImage(kadr.convert("RGB"))
            self.tlo.configure(image=self._tlo_tk)
        except (OSError, ValueError, MemoryError):
            # brak zdjecia nie moze przeszkodzic w zalogowaniu
            self.tlo.configure(image="", bg=B["tlo"])

    def komunikat(self, tekst, kolor=None):
        """Napis w rogu ekranu logowania: wersja albo postep aktualizacji."""
        try:
            self.stopka.configure(text=tekst, fg=kolor or B["zloto"])
        except tk.TclError:
            pass

    def postep(self, ulamek, tekst=""):
        """Zielony pasek wgrywania aktualizacji z procentami."""
        ulamek = max(0.0, min(1.0, float(ulamek)))
        try:
            if not self.ramka_postepu.winfo_ismapped():
                self.ramka_postepu.pack(fill="x", pady=(14, 0),
                                        before=self._lbl_fabryczny)
            self.lbl_postep.configure(
                text=f"{tekst}  {round(ulamek * 100)}%".strip())
            self.wypelnienie.place_configure(relwidth=ulamek)
        except (tk.TclError, AttributeError):
            pass

    def schowaj_postep(self):
        try:
            self.ramka_postepu.pack_forget()
        except (tk.TclError, AttributeError):
            pass

    # ---------------- karta ----------------

    def _buduj_karte(self):
        w = tk.Frame(self.karta, bg=B["tlo2"], padx=30, pady=22)
        w.pack()

        plik = zasob("godlo-awf.png")
        if plik:
            try:
                obraz = Image.open(plik).convert("RGBA").resize((62, 62),
                                                                Image.LANCZOS)
                self._godlo = ImageTk.PhotoImage(obraz)
                tk.Label(w, image=self._godlo, bg=B["tlo2"]).pack()
            except (OSError, ValueError):
                pass

        tk.Label(w, text=NAZWA, bg=B["tlo2"], fg=B["tekst"],
                 font=("Segoe UI Semibold", 15)).pack(pady=(10, 0))
        tk.Label(w, text=PODTYTUL, bg=B["tlo2"], fg=B["przygasz"],
                 font=("Segoe UI", 10)).pack()

        self.kropki = tk.Label(w, text="", bg=B["tlo2"], fg=B["akcentTekst"],
                               font=("Segoe UI", 18), height=1)
        self.kropki.pack(pady=(10, 0))
        self.info = tk.Label(w, text="", bg=B["tlo2"], fg=B["alarm"],
                             font=("Segoe UI", 9))
        self.info.pack()

        siatka = tk.Frame(w, bg=B["tlo2"])
        siatka.pack(pady=(8, 0))
        self.przyciski = []
        for i, znak in enumerate(self.KLAWISZE):
            glowny = znak == "OK"
            b = tk.Button(
                siatka, text=znak, width=4, relief="flat", bd=0,
                cursor="hand2",
                font=("Segoe UI Semibold", 18 if not glowny else 14),
                pady=9, activeforeground=B["tekst"],
                bg=B["akcent"] if glowny else B["tlo3"],
                fg=B["naAkcencie"] if glowny else (
                    B["alarm"] if znak == "C" else B["tekst"]),
                activebackground=B["akcent2"] if glowny else B["linia"],
                command=lambda z=znak: self.klik(z))
            b.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="nsew")
            self.przyciski.append(b)

        # Pasek wgrywania aktualizacji — normalnie schowany, pokazuje sie
        # dopiero wtedy, gdy program pobiera nowa wersje.
        self.ramka_postepu = tk.Frame(w, bg=B["tlo2"])
        self.lbl_postep = tk.Label(self.ramka_postepu, text="", bg=B["tlo2"],
                                   fg=B["akcentTekst"],
                                   font=("Segoe UI Semibold", 9))
        self.lbl_postep.pack(anchor="w")
        tor = tk.Frame(self.ramka_postepu, bg=B["linia"], height=6)
        tor.pack(fill="x", pady=(4, 0))
        tor.pack_propagate(False)
        self.wypelnienie = tk.Frame(tor, bg=B["akcentTekst"])
        self.wypelnienie.place(x=0, y=0, relwidth=0, relheight=1)

        self._lbl_fabryczny = tk.Label(
            w, text="PIN fabryczny 1234 — zmień po pierwszym logowaniu",
            bg=B["tlo2"], fg=B["przygasz"], font=("Segoe UI", 8))
        self._lbl_fabryczny.pack(pady=(12, 0))
        odn = tk.Label(w, text="Nie pamiętam PIN-u", bg=B["tlo2"],
                       fg=B["zloto"], font=("Segoe UI", 9, "underline"),
                       cursor="hand2")
        odn.pack(pady=(4, 0))
        odn.bind("<Button-1>", lambda _e: self._zapomnialem())

    # ---------------- obsluga ----------------

    def klik(self, znak):
        if znak == "C":
            self.wpisany = ""
        elif znak == "OK":
            self._sprawdz()
            return
        elif len(self.wpisany) < 8:
            self.wpisany += znak
        self.kropki.configure(text="●  " * len(self.wpisany))
        self.info.configure(text="")

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
            self.kropki.configure(text="")
            if self.proby >= 5:
                self.info.configure(text="Zablokowano — uruchom ponownie")
                for b in self.przyciski:
                    b.configure(state="disabled")
            else:
                self.info.configure(text=f"Błędny PIN — próba {self.proby} z 5")

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
        zastosuj_motyw(self.d.get("motyw") == "jasny")
        self.obiekt = 0
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

        # Aktualizacja wgrywa sie sama, jeszcze przed wpisaniem PIN-u.
        self._zalogowany = False
        self._akt_stan = None
        self.after(1200, self._cicha_aktualizacja)

        self.bind("<F11>", lambda _e: self.pelny_ekran())
        self.bind("<Escape>", self._escape)

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
        # Gdy sprawdzenie przed PIN-em juz powiedzialo, ze wersja jest
        # najnowsza, nie ma po co pytac serwera drugi raz.
        if self._akt_stan != "aktualna":
            self._sprawdz_aktualizacje()

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
        plik = zasob("logo-awf.png" if B["welon"] else "godlo-awf.png")
        if plik:
            obraz = Image.open(plik).convert("RGBA")
            if B["welon"]:
                h = 28
                obraz = obraz.resize((int(obraz.width * h / obraz.height), h),
                                     Image.LANCZOS)
            else:
                obraz = obraz.resize((36, 36), Image.LANCZOS)
            self._znak = ImageTk.PhotoImage(obraz)
            tk.Label(marka, image=self._znak, bg=B["tlo2"]).pack(side="left")

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
            self.gora, text="v" + VER, bg=B["tlo2"], fg=B["zloto"],
            font=("Segoe UI Semibold", 9), padx=8)
        self.lbl_wer_gora.pack(side="right")

        self.tresc = tk.Frame(self, bg=B["tlo"])
        self.tresc.pack(fill="both", expand=True)

        self.widoki = {}
        self.scena = Scena(self.tresc)
        self.scena.material = self.scena.wczytaj_material()
        self.scena.on_przycisk = self.przycisk_sceny
        self.widoki["podglad"] = self.scena
        for klucz in ("kierowcy", "sterownik", "historia", "ustawienia"):
            self.widoki[klucz] = tk.Frame(self.tresc, bg=B["tlo"])

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
            stopka, text=f"{self.d.get('nazwa', NAZWA)} {VER}  ·  Straż Akademicka",
            bg=B["tlo2"], fg=B["przygasz"], font=("Segoe UI", 8))
        self.lbl_wersja.pack(side="right", padx=14)

        self.przelacz("podglad")
        self._zmien_obiekt()

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
        r = tk.Frame(rodzic, bg=B["tlo"])
        r.pack(fill="x", padx=24, pady=(20, 14))
        tk.Label(r, text=tytul, bg=B["tlo"], fg=B["tekst"],
                 font=("Segoe UI Semibold", 15)).pack(anchor="w")
        tk.Label(r, text=podtytul, bg=B["tlo"], fg=B["przygasz"],
                 font=("Segoe UI", 9)).pack(anchor="w")

    def _tabela(self, rodzic, kolumny, szerokosci):
        ram = tk.Frame(rodzic, bg=B["tlo"])
        ram.pack(fill="both", expand=True, padx=24, pady=(0, 10))
        styl = ttk.Style()
        styl.theme_use("clam")
        styl.configure("AWF.Treeview", background=B["tlo2"],
                       fieldbackground=B["tlo2"], foreground=B["tekst"],
                       rowheight=30, borderwidth=0,
                       font=("Segoe UI", 10))
        styl.configure("AWF.Treeview.Heading", background=B["tlo3"],
                       foreground=B["przygasz"], relief="flat",
                       font=("Segoe UI Semibold", 8))
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
        r = tk.Frame(rodzic, bg=B["tlo"])
        r.pack(fill="x", padx=24, pady=(0, 18))
        for tekst, akcja, glowny in pozycje:
            tk.Button(r, text=tekst, command=akcja, relief="flat", bd=0,
                      cursor="hand2", font=("Segoe UI", 10), padx=16, pady=8,
                      bg=B["akcent"] if glowny else B["tlo3"],
                      fg=B["naAkcencie"] if glowny else B["tekst"],
                      activebackground=B["akcent2"] if glowny else B["linia"]
                      ).pack(side="left", padx=(0, 8))

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
                     font=("Segoe UI", 8), anchor="w").pack(anchor="w", padx=14,
                                                            pady=(12, 0))
            v = tk.Label(k, text="—", bg=B["tlo2"], fg=B["akcentTekst"],
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
                                   relief="flat", font=("Segoe UI", 10),
                                   insertbackground=B["tekst"], width=28)
        self.pole_nazwa.insert(0, self.d.get("nazwa", NAZWA))
        self.pole_nazwa.grid(row=1, column=0, sticky="w", ipady=5, padx=(0, 10))
        self.pole_podtytul = tk.Entry(siatka, bg=B["tlo3"], fg=B["tekst"],
                                      relief="flat", font=("Segoe UI", 10),
                                      insertbackground=B["tekst"], width=34)
        self.pole_podtytul.insert(0, self.d.get("podtytul", PODTYTUL))
        self.pole_podtytul.grid(row=1, column=1, sticky="w", ipady=5, padx=(0, 10))
        tk.Button(siatka, text="Zastosuj", command=self.zmien_nazwe,
                  relief="flat", bd=0, cursor="hand2", bg=B["akcent"],
                  fg=B["naAkcencie"], font=("Segoe UI", 10), padx=16, pady=6
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
                 bg=B["tlo2"], fg=B["przygasz"], font=("Segoe UI", 9),
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
                      cursor="hand2", font=("Segoe UI", 10), padx=14, pady=7,
                      bg=B["akcent"] if glowny else B["tlo3"],
                      fg=B["naAkcencie"] if glowny else B["tekst"],
                      activebackground=B["akcent2"] if glowny else B["linia"]
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
                       font=("Segoe UI", 10)).pack(anchor="w", padx=24,
                                                   pady=(0, 14))

        self._przyciski(w, [("Co nowego w kolejnych wersjach", self.okno_historii, False),
                            ("Zapisz kopię bazy", self.kopia_zapisz, False),
                            ("Wczytaj kopię", self.kopia_wczytaj, False),
                            ("Zmień PIN", self.zmien_pin, False),
                            ("Sprawdź aktualizacje", self.sprawdz_recznie, True)])
        self.lbl_akt = tk.Label(
            w, text=f"Wersja programu: {VER}  ·  jeszcze nie sprawdzano",
            bg=B["tlo"], fg=B["przygasz"], font=("Segoe UI", 10))
        self.lbl_akt.pack(anchor="w", padx=24)
        tk.Label(w, text="Program sprawdza aktualizacje sam, przy każdym "
                         "uruchomieniu, zaraz po zalogowaniu.",
                 bg=B["tlo"], fg=B["przygasz"],
                 font=("Segoe UI", 9)).pack(anchor="w", padx=24, pady=(4, 0))

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

    def _zmien_obiekt(self, _=None):
        stary = self.d["obiekty"][self.obiekt]["id"]
        self.stany[stary] = {"postep": self.scena.postep,
                             "faza": self.scena.faza,
                             "blokada": self.scena.zablokowana}
        self.obiekt = self.wyb_obiekt.current() if hasattr(self, "wyb_obiekt") else 0
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
        self.scena.rysuj()

    def przycisk_sceny(self, nr):
        if nr == 0:
            self.wpusc()
        elif nr == 1:
            self.recznie(True)
        elif nr == 2:
            self.recznie(False)
        else:
            self.blokada()

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
                self.scena.rysuj()
        except tk.TclError:
            pass
        self.after(1000, self._petla)

    # ---------------- narzedzia ----------------

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
            text=f'{self.d["nazwa"]} {VER}  ·  Straż Akademicka')
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
            self.log(f"zaktualizowano do wersji {tresc or VER}")
            nowa = tresc or VER
            self.after(600, lambda: self._pasek_informacyjny(
                f"Zaktualizowano do wersji {nowa}", B["akcent"]))
        else:
            self.log("aktualizacja nieudana: " + tresc)
            self.after(600, lambda: messagebox.showwarning(
                "Aktualizacja", tresc + "\n\nProgram działa w poprzedniej "
                "wersji.", parent=self))

    def _pasek_informacyjny(self, tekst, kolor):
        """Waski pasek u gory, znika sam po kilku sekundach."""
        pasek = tk.Frame(self, bg=kolor, height=34)
        pasek.pack(fill="x", before=self.tresc)
        pasek.pack_propagate(False)
        tk.Label(pasek, text=tekst, bg=kolor, fg=B["naAkcencie"],
                 font=("Segoe UI Semibold", 10)).pack(side="left", padx=18)
        tk.Label(pasek, text="✕", bg=kolor, fg=B["naAkcencie"],
                 font=("Segoe UI", 11), cursor="hand2", padx=16
                 ).pack(side="right")

        def zamknij(_e=None):
            try:
                pasek.destroy()
                self.scena.rysuj()
            except tk.TclError:
                pass
        for dziecko in pasek.winfo_children():
            dziecko.bind("<Button-1>", zamknij)
        pasek.bind("<Button-1>", zamknij)
        self.after(8000, zamknij)

    # ------- cicha aktualizacja przed zalogowaniem -------

    def _cicha_aktualizacja(self):
        """Sprawdza serwer i sam wgrywa nowa wersje, zanim ktos wpisze PIN.

        Na ekranie logowania nikt nie pracuje, wiec zamkniecie i ponowne
        uruchomienie programu niczego nie przerywa. W czasie sluzby juz tak
        nie robimy — wtedy tylko pytamy oknem.
        """
        try:
            import aktualizacje                      # noqa: F401
        except ImportError:
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
            self._wgraj_po_cichu(dane)
        elif rodzaj == "aktualna":
            self._napis_pin("v" + VER + " — najnowsza")
        else:
            self._napis_pin("v" + VER)

    def _napis_pin(self, tekst, kolor=None):
        """Napis w rogu ekranu logowania — po zalogowaniu juz go nie ma."""
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
        self._pasek_pin(0.0, f"Aktualizacja do {info['wersja']}")
        self._napis_pin(f"v{VER} → {info['wersja']}", B["akcent"])
        self.log(f'dostępna wersja {info["wersja"]} — wgrywam sama')

        def robota():
            import aktualizacje
            try:
                bat = aktualizacje.zainstaluj_po_cichu(
                    info,
                    postep=lambda u: self._kolejka_wgrania.put(("postep", u)))
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
            self._pasek_pin(tresc, f"Aktualizacja do {info['wersja']}")
            self.after(100, lambda: self._odbierz_wgranie(info))
            return

        if rodzaj == "blad":
            # Nieudane pobranie nie moze przeszkodzic w zalogowaniu.
            self._schowaj_pasek_pin()
            self._napis_pin("v" + VER)
            self.log("cicha aktualizacja nieudana: " + str(tresc))
            return

        if self._zalogowany:
            self._schowaj_pasek_pin()
            # Ktos zdazyl wpisac PIN w trakcie pobierania. Nie zamykamy
            # programu w czasie sluzby — podmiana poczeka do nastepnego
            # uruchomienia, pliki juz leza gotowe.
            self.log(f'wersja {info["wersja"]} pobrana — wgra się '
                     'przy następnym uruchomieniu')
            return

        self._pasek_pin(1.0, "Zamykam się — zaraz wrócę w nowej wersji")
        self.update_idletasks()
        import aktualizacje
        aktualizacje.uruchom_pomocnika(tresc)
        self.after(400, self.destroy)

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
            self.log(f"wersja {VER} — najnowsza")
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
        tk.Label(gora, text="masz " + VER, bg=B["tlo2"], fg=B["zloto"],
                 font=("Segoe UI Semibold", 10)).pack(side="right", padx=18)

        pole = tk.Text(w, bg=B["tlo"], fg=B["tekst"], relief="flat",
                       font=("Segoe UI", 10), padx=20, pady=16, wrap="word",
                       spacing1=2, spacing3=4)
        pas = ttk.Scrollbar(w, orient="vertical", command=pole.yview)
        pole.configure(yscrollcommand=pas.set)
        pas.pack(side="right", fill="y")
        pole.pack(fill="both", expand=True)

        pole.tag_configure("wersja", font=("Segoe UI Semibold", 13),
                           foreground=B["akcentTekst"], spacing1=14,
                           spacing3=2)
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


if __name__ == "__main__":
    App().mainloop()
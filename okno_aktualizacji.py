"""
WARTA AWF — okno powiadomienia o aktualizacji.

Do wklejenia do glownego pliku programu. Wymaga modulu `aktualizacje`.

Uzycie w programie glownym, w metodzie po zalogowaniu:

    import aktualizacje
    aktualizacje.sprawdz_w_tle(
        VER, lambda info: self.after(0, lambda: okno_aktualizacji(self, info)))

Sprawdzanie idzie w osobnym watku, wiec okno programu nie stoi. Wynik wraca
do watku glownego przez `after` — tkinter nie znosi grzebania w oknach
z innego watku.
"""

import queue
import threading
import tkinter as tk
from tkinter import ttk

import aktualizacje


def okno_aktualizacji(rodzic, info, kolory=None):
    """Pokazuje okno z opisem aktualizacji i obsluguje pobranie."""
    # Barwy uczelni: zielen #036744 jako wypelnienie, zloto #b9975b na
    # przycisk zatwierdzenia. Napis na zieleni bialy — zielen uczelni jest
    # za ciemna, zeby czytac na niej ciemny tekst.
    K = kolory or {
        "tlo": "#011c12", "tlo2": "#01291b", "linia": "#023c27",
        "tekst": "#ebf3f0", "przygaszony": "#86b6a5",
        "akcent": "#036744", "akcent2": "#024a31",
        "zloto": "#b9975b", "zloto2": "#e8d6b0", "naAkcencie": "#ffffff",
    }

    w = tk.Toplevel(rodzic)
    w.title("Dostępna aktualizacja")
    w.configure(bg=K["tlo"])
    w.resizable(False, False)
    w.transient(rodzic)
    w.grab_set()

    ramka = tk.Frame(w, bg=K["tlo"], padx=26, pady=22)
    ramka.pack(fill="both", expand=True)

    tk.Label(ramka, text=f"Dostępna wersja {info['wersja']}", bg=K["tlo"],
             fg=K["tekst"], font=("Segoe UI Semibold", 14)).pack(anchor="w")
    tk.Label(ramka, text="Program zaktualizuje się sam i uruchomi ponownie.",
             bg=K["tlo"], fg=K["przygaszony"],
             font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 14))

    if info.get("opis"):
        pole = tk.Text(ramka, height=7, width=54, bg=K["tlo2"], fg=K["tekst"],
                       relief="flat", padx=12, pady=10, wrap="word",
                       font=("Segoe UI", 10),
                       highlightthickness=1, highlightbackground=K["linia"])
        pole.insert("1.0", info["opis"])
        pole.configure(state="disabled")
        pole.pack(fill="x")

    stan = tk.Label(ramka, text="", bg=K["tlo"], fg=K["przygaszony"],
                    font=("Segoe UI", 9))
    stan.pack(anchor="w", pady=(12, 4))

    # Wlasny pasek zamiast ttk.Progressbar — ten drugi rysuje sie stylem
    # systemu i na Windows wychodzi bialo-niebieski, obcy wobec barw uczelni.
    pasek = tk.Frame(ramka, bg=K["tlo"])

    naglowek = tk.Frame(pasek, bg=K["tlo"])
    naglowek.pack(fill="x", pady=(0, 7))
    etap = tk.Label(naglowek, text="Pobieranie", bg=K["tlo"], fg=K["zloto2"],
                    font=("Segoe UI Semibold", 11))
    etap.pack(side="left")
    procent = tk.Label(naglowek, text="0%", bg=K["tlo"], fg=K["tekst"],
                       font=("Segoe UI Semibold", 16))
    procent.pack(side="right")

    tor = tk.Frame(pasek, bg=K["linia"], height=14, width=460)
    tor.pack(fill="x")
    tor.pack_propagate(False)
    wypelnienie = tk.Frame(tor, bg=K["akcent"])
    wypelnienie.place(x=0, y=0, relwidth=0, relheight=1)
    blask = tk.Frame(tor, bg=K["zloto"], height=2)
    blask.place(x=0, y=0, relwidth=0)

    def ustaw_postep(ulamek, opis=None):
        """Wypelnienie i procenty. Zloty wlos u gory daje wrazenie glebi."""
        u = max(0.0, min(1.0, float(ulamek)))
        wypelnienie.place_configure(relwidth=u)
        blask.place_configure(relwidth=u)
        procent.configure(text=f"{round(u * 100)}%")
        if opis:
            etap.configure(text=opis)

    guziki = tk.Frame(ramka, bg=K["tlo"])
    guziki.pack(fill="x", pady=(14, 0))

    def guzik(tekst, komenda, glowny=False):
        return tk.Button(
            guziki, text=tekst, command=komenda, relief="flat", bd=0,
            cursor="hand2", font=("Segoe UI Semibold", 10),
            padx=18, pady=9,
            bg=K["zloto"] if glowny else K["tlo2"],
            fg="#16301f" if glowny else K["tekst"],
            activebackground=K["zloto2"] if glowny else K["linia"],
            activeforeground="#16301f" if glowny else K["tekst"])

    def pozniej():
        w.destroy()

    # Watek roboczy nie dotyka okien — wklada wynik do kolejki,
    # a watek glowny co 120 ms zaglada, czy cos przyszlo. Wywolywanie
    # metod tkintera z obcego watku potrafi wywalic caly program.
    kolejka = queue.Queue()

    def instaluj():
        b_inst.configure(state="disabled")
        b_poz.configure(state="disabled")
        pasek.pack(fill="x", pady=(4, 10))
        ustaw_postep(0.0, "Pobieranie")
        stan.configure(text="Nie zamykaj programu do końca aktualizacji")

        def robota():
            try:
                plik = aktualizacje.pobierz(
                    info, postep=lambda u: kolejka.put(("postep", u)))
                kolejka.put(("etap", "Rozpakowywanie..."))
                nowe = aktualizacje.rozpakuj(plik)
                bat = aktualizacje.przygotuj_pomocnika(
                    nowe,
                    aktualizacje.katalog_programu(),
                    wersja=info.get("wersja", ""))
                kolejka.put(("gotowe", bat))
            except Exception as blad:
                kolejka.put(("blad", str(blad)))

        threading.Thread(target=robota, daemon=True).start()
        odbieraj()

    def odbieraj():
        try:
            while True:
                rodzaj, tresc = kolejka.get_nowait()
                if rodzaj == "postep":
                    ustaw_postep(tresc)
                elif rodzaj == "etap":
                    ustaw_postep(1.0, tresc.rstrip("."))
                elif rodzaj == "gotowe":
                    zakoncz(tresc)
                    return
                elif rodzaj == "blad":
                    niepowodzenie(tresc)
                    return
        except queue.Empty:
            pass
        w.after(120, odbieraj)

    def zakoncz(bat):
        ustaw_postep(1.0, "Gotowe")
        stan.configure(text="Zamykam program — wrócę za chwilę "
                            "w nowej wersji...")
        w.update_idletasks()
        aktualizacje.uruchom_pomocnika(bat)
        rodzic.after(400, rodzic.destroy)

    def niepowodzenie(tresc):
        pasek.pack_forget()
        stan.configure(text=f"Nie udało się: {tresc}", fg="#ff6b6b")
        b_inst.configure(state="normal", text="Spróbuj ponownie")
        b_poz.configure(state="normal")

    b_inst = guzik("Zainstaluj teraz", instaluj, glowny=True)
    b_inst.pack(side="right")

    b_poz = guzik("Przypomnij później", pozniej)
    b_poz.pack(side="right", padx=(0, 8))

    if info.get("wymagana"):
        b_poz.configure(state="disabled")
        tk.Label(guziki, text="Ta aktualizacja jest wymagana",
                 bg=K["tlo"], fg=K["zloto"],
                 font=("Segoe UI", 9)).pack(side="left")
        w.protocol("WM_DELETE_WINDOW", lambda: None)

    w.update_idletasks()
    x = rodzic.winfo_rootx() + (rodzic.winfo_width() - w.winfo_width()) // 2
    y = rodzic.winfo_rooty() + (rodzic.winfo_height() - w.winfo_height()) // 3
    w.geometry(f"+{max(0, x)}+{max(0, y)}")
    return w

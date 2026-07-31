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
    # Te same barwy uczelni co w programie glownym: zielen #036744
    # i zloto #b9975b. Napis na zieleni jest bialy — zielen uczelni jest
    # za ciemna, zeby czytac na niej ciemny tekst.
    K = kolory or {
        "tlo": "#011c12", "tlo2": "#01291b", "linia": "#023c27",
        "tekst": "#ebf3f0", "przygaszony": "#86b6a5",
        "akcent": "#036744", "akcent2": "#024a31",
        "zloto": "#b9975b", "naAkcencie": "#ffffff",
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

    pasek = ttk.Progressbar(ramka, length=460, mode="determinate", maximum=100)

    guziki = tk.Frame(ramka, bg=K["tlo"])
    guziki.pack(fill="x", pady=(14, 0))

    def guzik(tekst, komenda, glowny=False):
        return tk.Button(
            guziki, text=tekst, command=komenda, relief="flat", bd=0,
            cursor="hand2", font=("Segoe UI Semibold", 10),
            padx=18, pady=9,
            bg=K["akcent"] if glowny else K["tlo2"],
            fg=K["naAkcencie"] if glowny else K["tekst"],
            activebackground=K.get("akcent2", K["akcent"]) if glowny
            else K["linia"],
            activeforeground=K["naAkcencie"] if glowny else K["tekst"])

    def pozniej():
        w.destroy()

    # Watek roboczy nie dotyka okien — wklada wynik do kolejki,
    # a watek glowny co 120 ms zaglada, czy cos przyszlo. Wywolywanie
    # metod tkintera z obcego watku potrafi wywalic caly program.
    kolejka = queue.Queue()

    def instaluj():
        b_inst.configure(state="disabled")
        b_poz.configure(state="disabled")
        pasek.pack(fill="x", pady=(0, 6))
        stan.configure(text="Pobieranie...")

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
                    pasek.configure(value=round(tresc * 100))
                elif rodzaj == "etap":
                    stan.configure(text=tresc)
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

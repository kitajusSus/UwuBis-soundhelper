import os
import time
import random
from library import zapisz_wynik, rozpoznaj_slowa_z_pliku, powtorz_słowa, odtwarzaj_audio
import tkinter as tk
from tkinter import messagebox, filedialog
import openpyxl
import datetime
import threading

class Aplikacja:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacja UwuBiś")
        self.root.geometry("800x600") 
        self.login = tk.StringVar()
        self.wynik = tk.StringVar()
        self.czas_start = datetime.datetime.now()
        self.folder_zapisu = "wyniki/"  # Folder do zapisu wyników
        self.katalog_audio = ""  # Katalog z plikami audio (ustawiany przez użytkownika)
        self.ile_slow_do_rozpoznania = 5
        self.plik_audio = ""
        self.słowa_w_pliku = []
        self.rozdziały = []
        self.wyniki_użytkownika = {}
        self.ekrany = []
        self.aktualny_ekran = None

        self.login_screen()

    def login_screen(self):
        if self.aktualny_ekran:
            self.ekrany.append(self.aktualny_ekran)
            self.aktualny_ekran.pack_forget()

        self.aktualny_ekran = tk.Frame(self.root)
        self.aktualny_ekran.pack(fill="both", expand=True)

        tk.Label(self.aktualny_ekran, text="Login:").pack()
        tk.Entry(self.aktualny_ekran, textvariable=self.login).pack()
        tk.Button(self.aktualny_ekran, text="Zaloguj się", command=self.sprawdź_login).pack()
        tk.Button(self.aktualny_ekran, text="Cofnij", command=self.root.destroy).pack()

    def sprawdź_login(self):
        # Sprawdź login (tu powinna być logika sprawdzania loginu)
        if self.login.get() == "test":  # Przykładowy login
             self.wybierz_folder_audio_screen()
        else:
                messagebox.showerror("Błąd", "Niepoprawny login")

    def wybierz_folder_audio_screen(self):
        if self.aktualny_ekran:
            self.ekrany.append(self.aktualny_ekran)
            self.aktualny_ekran.pack_forget()

        self.aktualny_ekran = tk.Frame(self.root)
        self.aktualny_ekran.pack(fill="both", expand=True)

        tk.Button(self.aktualny_ekran, text="Wybierz folder z plikami audio", command=self.wybierz_folder_audio).pack()
        tk.Button(self.aktualny_ekran, text="Cofnij", command=self.cofnij).pack()

    def wybierz_folder_audio(self):
        self.katalog_audio = filedialog.askdirectory()
        self.pliki_audio_screen()

    def pliki_audio_screen(self):
        if self.aktualny_ekran:
            self.ekrany.append(self.aktualny_ekran)
            self.aktualny_ekran.pack_forget()

        self.aktualny_ekran = tk.Frame(self.root)
        self.aktualny_ekran.pack(fill="both", expand=True)

        self.pliki_audio = [f for f in os.listdir(self.katalog_audio) if f.endswith('.wav')]
        self.listbox = tk.Listbox(self.aktualny_ekran, width=80, height=20)  
        for plik in self.pliki_audio:
            self.listbox.insert(tk.END, plik)
        self.listbox.pack(pady=50)  
        tk.Button(self.aktualny_ekran, text="Wybierz plik audio", command=self.wybierz_plik_audio).pack(pady=10)
        tk.Button(self.aktualny_ekran, text="Cofnij", command=self.cofnij).pack(pady=10)

    def wybierz_plik_audio(self):
        self.plik_audio = os.path.join(self.katalog_audio, self.listbox.get(tk.ACTIVE))
        self.słowa_w_pliku = rozpoznaj_slowa_z_pliku(self.plik_audio, len(rozpoznaj_slowa_z_pliku(self.plik_audio, 1000)))
        self.rozdziały = [self.słowa_w_pliku[i:i + self.ile_slow_do_rozpoznania] for i in range(0, len(self.słowa_w_pliku), self.ile_slow_do_rozpoznania)]
        self.rozdziały_screen()

    def rozdziały_screen(self):
        if self.aktualny_ekran:
            self.ekrany.append(self.aktualny_ekran)
            self.aktualny_ekran.pack_forget()

        self.aktualny_ekran = tk.Frame(self.root)
        self.aktualny_ekran.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(self.aktualny_ekran)
        for i, rozdział in enumerate(self.rozdziały):
            self.listbox.insert(tk.END, f"Rozdział {i+1}: {' '.join(rozdział)}")
        self.listbox.pack()
        tk.Button(self.aktualny_ekran, text="Wybierz rozdział", command=self.wybierz_rozdział).pack()
        tk.Button(self.aktualny_ekran, text="Cofnij", command=self.cofnij).pack()
        self.wynik_label = tk.Label(self.aktualny_ekran, text="Wynik:")
        self.wynik_label.pack()

    def wybierz_rozdział(self):
        wybrany_rozdział = self.listbox.get(tk.ACTIVE)
        numer_rozdziału = int(wybrany_rozdział.split(":")[0].split()[-1]) - 1
        słowa_w_rozdziale = self.rozdziały[numer_rozdziału]
        if numer_rozdziału in self.wyniki_użytkownika:
            self.wynik_label['text'] = f"Wynik:  {self.wyniki_użytkownika[numer_rozdziału]}"
        else:
            self.wynik_label['text']= "Brak wyniku"
        threading.Thread(target=self.przebieg_testu, args=(numer_rozdziału,)).start()

    def przebieg_testu(self, numer_rozdziału):
        słowa_w_rozdziale = self.rozdziały[numer_rozdziału]
        self.informacja_screen(numer_rozdziału)

    def informacja_screen(self, numer_rozdziału):
        if self.aktualny_ekran:
            self.ekrany.append(self.aktualny_ekran)
            self.aktualny_ekran.pack_forget()

        self.aktualny_ekran = tk.Frame(self.root)
        self.aktualny_ekran.pack(fill="both", expand=True)

        tk.Label(self.aktualny_ekran, text="Za sekundę rozpocznie się odtwarzanie audio...", wraplength=400, justify=tk.CENTER).pack(pady=20)
        self.root.after(1000, lambda: self.odtwórz_audio_ikontynuuj(numer_rozdziału))  # Po sekundzie uruchom odtwarzanie audio

    def odtwórz_audio_ikontynuuj(self, numer_rozdziału):
        self.aktualny_ekran.pack_forget()
        odtwarzaj_audio(self.plik_audio)  # Odtwarzaj cały plik audio (do poprawy: odtwarzaj tylko wybrany rozdział)
        time.sleep(1)  # Czas na zastanowienie
        poprawne_slowa, powtórzone_słowa = powtorz_słowa(self.rozdziały[numer_rozdziału])
        wynik = f"{len(poprawne_slowa)}/{len(self.rozdziały[numer_rozdziału])}"
        self.wyniki_użytkownika[numer_rozdziału] = wynik
        self.zapytaj_o_dalsze(numer_rozdziału, wynik, poprawne_slowa, powtórzone_słowa, self.rozdziały[numer_rozdziału])
        

    def zapytaj_o_dalsze(self, numer_rozdziału, wynik, poprawne_słowa, powtórzone_słowa, słowa_w_rozdziale):
        if self.aktualny_ekran:
            self.ekrany.append(self.aktualny_ekran)
            self.aktualny_ekran.pack_forget()
        self.aktualny_ekran = tk.Frame(self.root)
        self.aktualny_ekran.pack(fill="both", expand=True)
        tk.Label(self.aktualny_ekran, text=f"Wynik: {wynik}").pack()

        zapisz_wynik(self.login.get(), self.plik_audio, słowa_w_rozdziale, powtórzone_słowa, wynik, self.folder_zapisu)

        self.wyświetl_statystyki(słowa_w_rozdziale, poprawne_słowa, powtórzone_słowa)
        tk.Button(self.aktualny_ekran, text="Wybierz kolejny rozdział", command=self.rozdziały_screen).pack()
        tk.Button(self.aktualny_ekran, text="Cofnij", command=self.cofnij).pack()
        frame = tk.Frame(self.aktualny_ekran)
        frame.pack(pady=10)
        tk.Button(frame, text="Powtórz to samo audio", command=lambda: self.powtórz_audio(numer_rozdziału)).pack(side=tk.LEFT, padx=10)
        tk.Button(frame, text="Wybierz inny plik audio", command=self.wybierz_folder_audio_screen).pack(side=tk.LEFT, padx=10)
        tk.Button(frame, text="Zobacz statystyki i zakończ", command=lambda: self.wyświetl_statystyki_i_zakończ(słowa_w_rozdziale, poprawne_słowa, powtórzone_słowa)).pack(side=tk.LEFT, padx=10)

    def cofnij(self):
        if self.ekrany:
            self.aktualny_ekran.pack_forget()
            self.aktualny_ekran = self.ekrany.pop()

    def powtórz_audio(self, numer_rozdziału):
        self.root.destroy()
        threading.Thread(target=self.przebieg_testu, args=(numer_rozdziału,)).start()

    def wyświetl_statystyki_i_zakończ(self, słowa_w_rozdziale, poprawne_słowa, powtórzone_słowa):
        #self.save_current_screen()
        self.root.destroy()
        self.root = tk.Tk()
        self.root.title("Aplikacja UwuBiś - Statystyki")
        self.statystyki_text = tk.Text(self.root, height=15, width=60)
        self.statystyki_text.pack(pady=20)
        self.statystyki_text.insert(tk.END, f"Poprawnie powtórzone słowa: {len(poprawne_słowa)}/{len(słowa_w_rozdziale)}\n")
        for i, (słowo, powtórzone) in enumerate(zip(słowa_w_rozdziale, powtórzone_słowa), start=1):
             self.statystyki_text.insert(tk.END, f"{i}. {słowo} -> {powtórzone}\n")
        tk.Button(self.root, text="Zakończ", command=self.root.destroy).pack(pady=10)
        tk.Button(self.root, text="Cofnij", command=self.go_back).pack(pady=10)
        self.root.mainloop()

    def wyświetl_statystyki(self, słowa_w_rozdziale, poprawne_słowa, powtórzone_słowa):
        self.statystyki_text = tk.Text(self.root, height=10, width=40)
        self.statystyki_text.pack()
        self.statystyki_text.insert(tk.END, f"Poprawnie powtórzone słowa: {len(poprawne_słowa)}/{len(słowa_w_rozdziale)}\n")
        for i, (słowo, powtórzone) in enumerate(zip(słowa_w_rozdziale, powtórzone_słowa), start=1):
            self.statystyki_text.insert(tk.END, f"{i}. {słowo} -> {powtórzone}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = Aplikacja(root)
    root.mainloop()
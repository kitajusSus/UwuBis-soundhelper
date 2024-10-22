import os
import time
import random
from library import zapisz_wynik, rozpoznaj_slowa_z_pliku, losuj_plik_audio, powtorz_słowa, odtwarzaj_audio


class Main:
    def run(self):
        login = input("Podaj swój login: ")
        katalog_audio = "audio/"  # Zmień na odpowiednią ścieżkę
        folder_zapisu = "wyniki/"  # Zmień na odpowiednią ścieżkę
        ile_slow_do_rozpoznania = 5
        # Losuj plik audio
        nazwa_pliku = losuj_plik_audio(katalog_audio)
        print(f"Wybrany plik audio: {nazwa_pliku}")

        # Wczytaj słowa z pliku
        słowa = rozpoznaj_slowa_z_pliku(nazwa_pliku, ile_slow_do_rozpoznania)
        if not słowa:
            print("Nie udało się rozpoznać słów z pliku.")
            return
        
        # odtwarzanie audio dla użytkownika
        print("Odtwarzam audio...")
        odtwarzaj_audio(nazwa_pliku)
        # Input dla odpowiedzi użytkownika
        print("Za chwile rozpocznie sie nagrywanie twojej odpowiedzi.")
        time.sleep(1)  # czas na zastanowienie
        poprawne_słowa, powtórzone_słowa = powtorz_słowa(słowa)

        # Wyświetl słowa powiedziane poprawnie przez użytkownika
        print(f"\nPoprawnie powtórzone słowa: {' '.join(poprawne_słowa)}")

        # Wyświetl wszystkie słowa z pliku
        # print(f"Wszystkie słowa z pliku: {' '.join(słowa)}")
        print(f"Wynik: {len(poprawne_słowa)}/{ile_slow_do_rozpoznania}")
        # Zapisz wynik do pliku xlsx
        zapisz_wynik(login, poprawne_słowa, powtórzone_słowa, słowa)
if __name__ == "__main__":
    Main().run()
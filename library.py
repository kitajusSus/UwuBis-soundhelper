import os
import pandas as pd
import openpyxl
import soundfile as sf
import sounddevice as sd
import speech_recognition as sr
import time
import random


"""Funkcje pomocnicze do programu UwuBiś."""

def zapisz_wynik(login, nazwa_audio, poprawne_słowa, powtórzone_słowa, słowa, folder_zapisu):
    nazwa_pliku = f"{login}.xlsx"
    # Upewnij się, że folder zapisu istnieje
    if not os.path.exists(folder_zapisu):
        os.makedirs(folder_zapisu)
    
    # Jeśli nie istnieje plik to zrób nowy 
    if not os.path.exists(nazwa_pliku):
        # tworznie nagłówków df=dataframe
        df = pd.DataFrame(columns=["Numer podejścia","Nazwa Pliku i rozdzial" "Słowa w pliku", "Słowa poprawne", "Słowa niepoprawne", "Wynik", "Maksymalny Wynik"])
        df.to_excel(nazwa_pliku, index=False, engine='openpyxl')
    
    # Otwórz istniejący plik
    book = openpyxl.load_workbook(nazwa_pliku)
    sheet = book.active 
    # Numer podejścia
    numer_podejscia = sheet.max_row
    # Słowa niepoprawne lub pominięte
    niepoprawne_słowa = [s for s in powtórzone_słowa if s not in poprawne_słowa]
    # Wynik
    wynik = f"{len(poprawne_słowa)}/{len(słowa)}"
    maks_wynik = len(słowa) # ilość słow w pliku może się zmieniać ale narazie program czyta tylko pierwsze 5 słów
    # Dodaj nowy wiersz
    new_row = [numer_podejscia, ', ' .join(nazwa_audio), ', '.join(słowa), ', '.join(poprawne_słowa), ', '.join(niepoprawne_słowa), wynik, maks_wynik]
    sheet.append(new_row)
    # Zapisz plik
    book.save(nazwa_pliku)




def rozpoznaj_slowa_z_pliku(nazwa_pliku, ile_slow_do_rozpoznania):
    r = sr.Recognizer()
    with sr.AudioFile(nazwa_pliku) as source:
        audio = r.record(source)
        try:
            text = r.recognize_google(audio, language="pl-PL")
            słowa = text.split()[:ile_slow_do_rozpoznania]
            return słowa
        except sr.UnknownValueError:
            print("Nie rozpoznano żadnych słów.")
            return []
        

def losuj_plik_audio(katalog):
    pliki = [f for f in os.listdir(katalog) if f.endswith('.wav')]
    return os.path.join(katalog, random.choice(pliki))

def powtorz_słowa(słowa):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Powtórz słowa, które usłyszałeś:")
         # n = 10  definiowanie ilości sekund na powiedzenie słów
        r.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        audio = r.listen(source, timeout=10)  # n sekund na powiedzenie słow + uruchamianie mikrofonu

        """for i in range(n):
            print(f"Zostało {n} sekund")
            time.sleep(1)""" #pomysł na odliczanie czasu do konca nagrywania w timeout wstawiamy 
        #n i n definiujemy na podstawie długosci pliku audio
        
        try:
            powtórzone_słowa = r.recognize_google(audio, language="pl-PL").split()
            poprawne_słowa = list(set(słowa) & set(powtórzone_słowa))
            return poprawne_słowa, powtórzone_słowa
        except sr.UnknownValueError:
            print("Program UwuBiś nie rozpoznał żadnych słów, które powiedziałeś.")
            return [], []
        except sr.RequestError as e:
            print(f"Błąd połączenia z serwerem rozpoznawania mowy: {e}")
            return [], []

def odtwarzaj_audio(nazwa_pliku):
    """Odtwarza plik audio."""
    data, fs = sf.read(nazwa_pliku, dtype='float32')
    sd.play(data, fs)
    sd.wait()


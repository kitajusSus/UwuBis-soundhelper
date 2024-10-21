import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
import time

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

def powtorz_słowa(słowa):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Powtórz słowa, które usłyszałeś:")
        audio = r.listen(source)
        try:
            powtórzone_słowa = r.recognize_google(audio, language="pl-PL").split()
            poprawne_słowa = [s for s, ps in zip(słowa, powtórzone_słowa) if s.lower() == ps.lower()]
            return poprawne_słowa, powtórzone_słowa
        except sr.UnknownValueError:
            print("Program UwuBiś nie rozpoznał żadnych słów, które powiedziałeś.")
            return [], []

def odtwarzaj_audio(nazwa_pliku):
    """Odtwarza plik audio."""
    data, fs = sf.read(nazwa_pliku, dtype='float32')
    sd.play(data, fs)
    sd.wait()

def main():
    nazwa_pliku = "test1_.wav"  # nazwa pliku
    ile_slow_do_rozpoznania = 5
    
    # Wczytaj słowa z pliku
    słowa = rozpoznaj_slowa_z_pliku(nazwa_pliku, ile_slow_do_rozpoznania)
    if not słowa:
        print("Nie udało się rozpoznać słów z pliku.")
        return
    # Odtwórz audio dla użytkownika
    print("Odtwarzam audio...")
    odtwarzaj_audio(nazwa_pliku)

    # Pozwól użytkownikowi powtórzyć słowa
    print("Za chwile rozpocznie sie nagrywanie twojej odpowiedzi.")
    time.sleep(1)  # Krótka przerwa przed rozpoczęciem nagrywania
    poprawne_słowa, powtórzone_słowa = powtorz_słowa(słowa)

    # Wyświetl słowa powiedziane poprawnie przez użytkownika
    print(f"\nPoprawnie powtórzone słowa: {' '.join(poprawne_słowa)}")
    
    # Wyświetl wszystkie słowa z pliku
    print(f"Wszystkie słowa z pliku: {' '.join(słowa)}")
    print(f"Wynik: {len(poprawne_słowa)}/{ile_slow_do_rozpoznania}")

if __name__ == "__main__":
    main()
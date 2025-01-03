from pydub import AudioSegment
import os

def podziel_plik_audio(sciezka_do_pliku, sekundy_na_plik):
    """
    Dzieli plik audio na mniejsze pliki o określonej długości.
    
    :param sciezka_do_pliku: Ścieżka do pliku .wav
    :param sekundy_na_plik: Długość każdego wyodrębnionego pliku w sekundach
    """
    # Wczytaj plik audio
    sound = AudioSegment.from_wav(sciezka_do_pliku)
    
    # Pobierz długość pliku audio w sekundach
    dlugosc_pliku = len(sound) / 1000  # Przelicz z milisekund na sekundy
    
    # Oblicz liczbę plików, które będą wygenerowane
    liczba_plikow = int(dlugosc_pliku // sekundy_na_plik) + (1 if dlugosc_pliku % sekundy_na_plik != 0 else 0)
    
    # Pobierz nazwę pliku bez rozszerzenia
    nazwa_pliku = os.path.splitext(sciezka_do_pliku)[0]
    
    # Dziel plik
    for i in range(liczba_plikow):
        start = i * sekundy_na_plik * 1000  # Przelicz sekundy na milisekundy
        end = (i + 1) * sekundy_na_plik * 1000 if (i + 1) * sekundy_na_plik <= dlugosc_pliku else len(sound)
        
        # Wyodrębnij fragment pliku
        fragment = sound[start:end]
        
        # Zapisz fragment jako nowy plik
        nazwa_nowego_pliku = f"{nazwa_pliku}_czesc_{i+1}.wav"
        fragment.export(nazwa_nowego_pliku, format="wav")
        
        print(f"Zapisano: {nazwa_nowego_pliku}")

# Przykład użycia
sciezka_do_pliku = "audio/demony/31wiele_demonow.wav"  # Wstaw swoją ścieżkę
sekundy_na_plik = 5  # Długość każdego pliku w sekundach
podziel_plik_audio(sciezka_do_pliku, sekundy_na_plik)
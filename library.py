import os
import pandas as pd
import openpyxl
import soundfile as sf
import sounddevice as sd
import speech_recognition as sr
import time
import random
import pygame
import logging
import threading
from tempfile import NamedTemporaryFile

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

"""
Funkcje pomocnicze do programu UwuBiś.
"""

class AudioHelper:
    def __init__(self, config):
        self.config = config
        self.audio_duration = 0
        self.current_chapter = 0
        self.słowa_w_pliku = []
        self.rozdziały = []

    def load_audio_file(self, file_path):
        """Ładuje plik audio i przygotowuje rozdziały."""
        try:
            audio_data, samplerate = sf.read(file_path)
            self.audio_duration = len(audio_data) / samplerate
            self.słowa_w_pliku = rozpoznaj_slowa_z_pliku(file_path)
            self.current_chapter = 0
            self.rozdziały = [
                self.słowa_w_pliku[i:i + self.config.WORDS_PER_CHAPTER] 
                for i in range(0, len(self.słowa_w_pliku), self.config.WORDS_PER_CHAPTER)
            ]
            return True
        except Exception as e:
            logging.error(f"Błąd podczas ładowania pliku audio: {str(e)}")
            return False

    def get_audio_files(self, folder_path):
        """Zwraca listę plików audio w folderze."""
        try:
            return [f for f in os.listdir(folder_path) if f.endswith('.wav')]
        except Exception as e:
            logging.error(f"Błąd podczas listowania plików audio: {str(e)}")
            return []

    def play_chapter(self, chapter_idx, file_path):
        """Odtwarza rozdział audio."""
        try:
            start_time = chapter_idx * self.config.DEFAULT_SEGMENT_DURATION
            current_words = self.rozdziały[chapter_idx]
            
            audio_thread = threading.Thread(
                target=odtwarzaj_audio,
                kwargs={
                    'plik_audio': file_path,
                    'words': current_words,
                    'start_time': start_time,
                    'duration': self.config.DEFAULT_SEGMENT_DURATION
                }
            )
            audio_thread.start()
            audio_thread.join()
            return current_words
        except Exception as e:
            logging.error(f"Błąd podczas odtwarzania rozdziału: {str(e)}")
            return []

    def has_next_chapter(self):
        """Sprawdza czy istnieje następny rozdział."""
        return self.current_chapter < len(self.rozdziały)

    def get_current_words(self):
        """Zwraca słowa z aktualnego rozdziału."""
        if self.current_chapter < len(self.rozdziały):
            return self.rozdziały[self.current_chapter]
        return []

def zapisz_wynik(login, nazwa_audio, poprawne_słowa, powtórzone_słowa, słowa, folder_zapisu):
    """
    Zapisuje wyniki testu do pliku Excel.
    """
    try:
        os.makedirs(folder_zapisu, exist_ok=True)
        nazwa_pliku = os.path.join(folder_zapisu, f"{login}.xlsx")
        
        df_new = pd.DataFrame({
            "Numer podejścia": [pd.read_excel(nazwa_pliku).shape[0] + 1] if os.path.exists(nazwa_pliku) else [1],
            "Nazwa Pliku i rozdział": [nazwa_audio],
            "Słowa w pliku": [', '.join(słowa)],
            "Słowa poprawne": [', '.join(poprawne_słowa)],
            "Słowa niepoprawne": [', '.join(set(słowa) - set(poprawne_słowa))],
            "Wynik": [f"{len(poprawne_słowa)}/{len(słowa)}"],
            "Maksymalny Wynik": [len(słowa)]
        })
        
        if os.path.exists(nazwa_pliku):
            df_existing = pd.read_excel(nazwa_pliku)
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_final = df_new
        
        df_final.to_excel(nazwa_pliku, index=False)
        logging.info(f"Zapisano wynik dla użytkownika {login}")
    except Exception as e:
        logging.error(f"Błąd podczas zapisywania wyniku: {str(e)}")
        raise

def rozpoznaj_slowa_z_pliku(nazwa_pliku, ile_slow=5):
    """
    Rozpoznaje słowa z pliku audio.
    """
    r = sr.Recognizer()
    try:
        with sr.AudioFile(nazwa_pliku) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="pl-PL")
            words = text.split()
            return words[:ile_slow]
    except sr.UnknownValueError:
        logging.warning("Nie rozpoznano żadnych słów.")
        return []
    except Exception as e:
        logging.error(f"Błąd podczas rozpoznawania słów: {str(e)}")
        return []

def losuj_plik_audio(katalog):
    """
    Losuje plik audio z podanego katalogu.
    """
    try:
        pliki = [f for f in os.listdir(katalog) if f.endswith('.wav')]
        if not pliki:
            raise ValueError("Brak plików audio w katalogu")
        return os.path.join(katalog, random.choice(pliki))
    except Exception as e:
        logging.error(f"Błąd podczas losowania pliku: {str(e)}")
        raise

def powtorz_słowa(słowa):
    """
    Nagrywa i rozpoznaje powtórzone słowa użytkownika.
    """
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            logging.info("Rozpoczęto nagrywanie")
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, timeout=10)
            
            powtórzone_słowa = r.recognize_google(audio, language="pl-PL").split()
            poprawne_słowa = list(set(słowa) & set(powtórzone_słowa))
            return poprawne_słowa, powtórzone_słowa
    except sr.UnknownValueError:
        logging.warning("Nie rozpoznano żadnych słów")
        return [], []
    except sr.RequestError as e:
        logging.error(f"Błąd połączenia z serwerem rozpoznawania mowy: {str(e)}")
        return [], []
    except Exception as e:
        logging.error(f"Nieoczekiwany błąd: {str(e)}")
        return [], []

def odtwarzaj_audio(plik_audio, words, start_time=0, duration=5):
    """
    Odtwarza fragment pliku audio.
    """
    temp_file_path = None
    try:
        data, samplerate = sf.read(plik_audio)
        start_frame = int(start_time * samplerate)
        duration_frames = int(duration * samplerate)
        segment = data[start_frame:start_frame + duration_frames]
        
        # Create temporary file with absolute path
        temp_file_path = os.path.abspath(os.path.join(
            os.path.dirname(plik_audio),
            f'temp_segment_{int(time.time())}.wav'
        ))
        
        # Write audio segment to temporary file
        sf.write(temp_file_path, segment, samplerate)
        
        # Initialize pygame mixer
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file_path)
        pygame.mixer.music.play()
        
        # Wait for playback to complete
        time.sleep(duration)
        pygame.mixer.music.stop()
            
    except Exception as e:
        logging.error(f"Błąd odtwarzania audio: {str(e)}")
        raise
    finally:
        pygame.mixer.quit()
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logging.error(f"Nie udało się usunąć pliku tymczasowego: {str(e)}")


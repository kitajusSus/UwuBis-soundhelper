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

class AUDIOLIB:
    def __init__(self, config):
        self.config = config
        self.audio_duration = 0
        self.current_segment = 0
        self.słowa_w_pliku = []
        self.segments = []
        self.current_segment_audio = None  # Store current segment audio data
        self.current_segment_sr = None     # Store current segment sample rate
        self.segment_positions = []  # Store start positions for each segment

    def load_audio_file(self, file_path):
        """Ładuje plik audio i dzieli na 5-słowne segmenty."""
        try:
            self.audio_data, self.samplerate = sf.read(file_path)
            self.audio_duration = len(self.audio_data) / self.samplerate
            self.słowa_w_pliku = rozpoznaj_slowa_z_pliku(file_path)
            self.current_segment = 0
            
            # Calculate segment positions and durations
            total_duration = self.audio_duration
            segment_duration = total_duration / len(self.słowa_w_pliku)
            
            # Divide words into segments and store their positions
            self.segments = []
            self.segment_positions = []
            for i in range(0, len(self.słowa_w_pliku), 5):
                segment = self.słowa_w_pliku[i:i + 5]
                if segment:
                    self.segments.append(segment)
                    start_pos = i * segment_duration
                    self.segment_positions.append(start_pos)
            
            return True
        except Exception as e:
            logging.error(f"Blad podczas ladowania pliku audio: {str(e)}")
            return False

    def play_segment(self, segment_idx, file_path):
        """Odtwarza segment audio."""
        try:
            if segment_idx >= len(self.segment_positions):
                return []
                
            start_time = self.segment_positions[segment_idx]
            duration = self.config.DEFAULT_SEGMENT_DURATION
            current_words = self.segments[segment_idx]
            
            # Calculate and store segment audio
            start_frame = int(start_time * self.samplerate)
            duration_frames = int(duration * self.samplerate)
            self.current_segment_audio = self.audio_data[start_frame:start_frame + duration_frames]
            self.current_segment_sr = self.samplerate
            
            self._play_segment_audio()
            return current_words
        except Exception as e:
            logging.error(f"Blad podczas odtwarzania segmentu: {str(e)}")
            return []

    def replay_current_segment(self):
        """Powtarza odtwarzanie aktualnego segmentu."""
        if self.current_segment_audio is not None:
            try:
                self._play_segment_audio()
                return True
            except Exception as e:
                logging.error(f"Blad podczas powtarzania segmentu: {str(e)}")
        return False

    def _play_segment_audio(self):
        """Wewnętrzna metoda do odtwarzania segmentu."""
        temp_file_path = None
        try:
            temp_file_path = os.path.abspath(f'temp_segment_{int(time.time())}.wav')
            sf.write(temp_file_path, self.current_segment_audio, self.current_segment_sr)
            
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            time.sleep(self.config.DEFAULT_SEGMENT_DURATION)
            pygame.mixer.music.stop()
        finally:
            pygame.mixer.quit()
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logging.error(f"Nie udało się usunąć pliku tymczasowego: {str(e)}")

    def get_total_segments(self):
        """Zwraca całkowitą liczbę segmentów."""
        return len(self.segments)

    def get_current_segment_words(self):
        """Zwraca słowa z aktualnego segmentu."""
        if 0 <= self.current_segment < len(self.segments):
            return self.segments[self.current_segment]
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
        logging.error(f"Blad podczas zapisywania wyniku: {str(e)}")
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
        logging.warning("Nie rozpoznano zadnych slow.")
        return []
    except Exception as e:
        logging.error(f"Blad podczas rozpoznawania slow: {str(e)}")
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
        logging.error(f"Blad podczas losowania pliku: {str(e)}")
        raise

def powtorz_słowa(słowa, timeout=None):
    """
    Nagrywa i rozpoznaje powtórzone słowa użytkownika.
    """
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            logging.info("Rozpoczęto nagrywanie")
            r.adjust_for_ambient_noise(source)
            # Używamy timeout z GUI jeśli jest podany
            audio = r.listen(source, timeout=timeout if timeout else 10)
            
            powtórzone_słowa = r.recognize_google(audio, language="pl-PL").split()
            poprawne_słowa = list(set(słowa) & set(powtórzone_słowa))
            return poprawne_słowa, powtórzone_słowa
    except sr.WaitTimeoutError:
        logging.warning("Przekroczono czas oczekiwania na mowę")
        return [], []
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


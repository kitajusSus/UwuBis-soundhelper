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
        self.current_segment_words = []
        self.segment_duration = 5  # Duration for each 5-word segment
        self.segment_words_dict = {}  # Add dictionary to store words for each segment
        self.word_timestamps = {}  # miejsce do przechowywania słów z czasami
        self.total_segments = 0  # Add place to store number of segments 
        self.words_with_timestamps = []  # Add new attribute to store word timings

    def load_audio_file(self, file_path):
        """Ładuje plik audio i dzieli na 5-słowne segmenty."""
        try:
            # Load audio file
            self.audio_data, self.samplerate = sf.read(file_path)
            self.audio_duration = len(self.audio_data) / self.samplerate
            
            # Get words with timestamps
            self.words_with_timestamps = self._recognize_words_with_timestamps(file_path)
            if not self.words_with_timestamps:
                logging.error("Nie rozpoznano żadnych słów w pliku")
                return False
            
            # Extract just the words for reference
            self.słowa_w_pliku = [word for word, _, _ in self.words_with_timestamps]
            
            # Reset segment containers
            self.segments = []
            self.segment_words_dict = {}
            self.segment_positions = []
            
            # Split into 5-word segments
            words_per_segment = 5
            total_words = len(self.words_with_timestamps)
            
            for i in range(0, total_words, words_per_segment):
                segment_words = self.words_with_timestamps[i:i + words_per_segment]
                if not segment_words:
                    continue
                
                # Get start and end times for this segment
                segment_start = segment_words[0][1]  # First word start time
                segment_end = segment_words[-1][2]   # Last word end time
                
                # Convert times to frames
                start_frame = max(0, int(segment_start * self.samplerate))
                end_frame = min(len(self.audio_data), int(segment_end * self.samplerate))
                
                # Add silence buffer (0.2 seconds)
                silence_buffer = int(0.2 * self.samplerate)
                start_frame = max(0, start_frame - silence_buffer)
                end_frame = min(len(self.audio_data), end_frame + silence_buffer)
                
                # Create segment
                segment_audio = self.audio_data[start_frame:end_frame]
                self.segments.append(segment_audio)
                
                # Store segment words (just the words, not timestamps)
                segment_idx = len(self.segments) - 1
                self.segment_words_dict[segment_idx] = [word for word, _, _ in segment_words]
                self.segment_positions.append(segment_start)
                ## giga combo jest, bedzie trudno
                logging.info(f"Segment {segment_idx + 1}: {self.segment_words_dict[segment_idx]}")
            
            self.total_segments = len(self.segments)
            logging.info(f"Utworzono {self.total_segments} segmentów po {words_per_segment} słów")
            return True
            
        except Exception as e:
            logging.error(f"Błąd podczas ładowania pliku audio: {str(e)}")
            return False

    def play_segment(self, segment_idx, file_path):
        """Odtwarza segment audio."""
        try:
            if (segment_idx >= len(self.segments)):
                return []
                
            self.current_segment = segment_idx
            self.current_segment_audio = self.segments[segment_idx]
            self.current_segment_sr = self.samplerate
            
            # Play segment and return its words
            self._play_segment_audio()
            return self.get_current_segment_words()
            
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
           
            # Czekaj na zakończenie aktualnego segmentu
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Dodaj większe opóźnienie na końcu
            time.sleep(0.3)
            
        finally:
            pygame.mixer.quit()
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logging.error(f"Nie udało się usunąć pliku tymczasowego: {str(e)}")
                    
    def _recognize_words_with_timestamps(self, file_path):
        """Rozpoznaje słowa wraz z ich czasami początku i końca."""
        r = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                audio = r.record(source)
                # Get initial word recognition
                text = r.recognize_google(audio, language="pl-PL")
                words = text.split()
                
                # Estimate timestamps based on audio duration
                word_count = len(words)
                if word_count == 0:
                    return []
                
                avg_duration = self.audio_duration / word_count
                timestamps = []
                
                for i, word in enumerate(words):
                    start_time = i * avg_duration
                    end_time = (i + 1) * avg_duration
                    timestamps.append((word, start_time, end_time))
                
                return timestamps
                
        except Exception as e:
            logging.error(f"Błąd podczas rozpoznawania słów z czasami: {str(e)}")
            return []

    def get_total_segments(self):
        """Zwraca całkowitą liczbę segmentów."""
        return self.total_segments

    def get_current_segment_words(self):
        """Zwraca słowa z aktualnego segmentu."""
        if self.current_segment in self.segment_words_dict:
            return self.segment_words_dict[self.current_segment]
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

def rozpoznaj_slowa_z_pliku(nazwa_pliku, ile_slow=None):
    """Rozpoznaje wszystkie słowa z pliku audio."""
    r = sr.Recognizer()
    try:
        with sr.AudioFile(nazwa_pliku) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="pl-PL")
            words = text.split()
            return words[:ile_slow] if ile_slow is not None else words
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
    """Nagrywa i rozpoznaje powtórzone słowa użytkownika."""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            logging.info("Rozpoczęto nagrywanie")
            r.adjust_for_ambient_noise(source)
            # Explicitly set both timeout and phrase_time_limit to the same value
            audio = r.listen(source, timeout=10.0, phrase_time_limit=10.0)
            
            # Add small delay before speech recognition to ensure full recording
            time.sleep(0.1)
            
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


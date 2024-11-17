import os
import pandas as pd
import soundfile as sf
import speech_recognition as sr
import time
import logging
import threading
import numpy as np
import pygame

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AUDIOLIB:

    def __init__(self, config):
        self.config = config
        self.audio_data = None
        self.samplerate = None
        self.words = []
        self.segments = []
        self.segment_words_dict = {}
        self.current_segment = 0
        self.total_segments = 0
        self.current_segment_audio = None
        self.word_matrix = None
        self.segment_status = {}
        self.temp_storage = {}

    def load_audio_file(self, file_path):
        """Loads audio file and segments it based on word count."""
        try:
            # Load audio file
            self.audio_data, self.samplerate = sf.read(file_path)

            # Get words from audio
            self.words = self._recognize_words(file_path)
            if not self.words:
                logging.error("No words recognized in file")
                return False

            # Create segments based on word count
            words_per_segment = 5  # Ensure each segment has exactly 5 words
            self.segments = []
            self.segment_words_dict = {}

            for i in range(0, len(self.words), words_per_segment):
                segment_words = self.words[i:i + words_per_segment]
                if len(segment_words) == words_per_segment:
                    self.segment_words_dict[len(self.segments)] = segment_words
                    self.segments.append(i // words_per_segment)

            self.total_segments = len(self.segments)
            self.current_segment = 0

            # Store current segment audio for replay functionality
            if self.total_segments > 0:
                self._update_current_segment_audio()

            logging.info(f"Created {self.total_segments} segments of {words_per_segment} words each")

            # Create word matrix (segments x 5 words)
            total_possible_segments = len(self.words) // 5
            self.word_matrix = np.empty((total_possible_segments, 5), dtype=object)
            self.segment_status = {}
            self.segment_words_dict = {}

            segment_idx = 0
            for i in range(0, len(self.words), 5):
                segment_words = self.words[i:i+5]
                if len(segment_words) == 5:  # Only store complete segments
                    self.word_matrix[segment_idx] = segment_words
                    self.segment_words_dict[segment_idx] = segment_words
                    self.segment_status[segment_idx] = False  # Not completed
                    segment_idx += 1

            self.total_segments = segment_idx
            self.current_segment = 0

            # Store first segment audio
            if self.total_segments > 0:
                self._update_current_segment_audio()

            return True

        except Exception as e:
            logging.error(f"Error loading audio file: {str(e)}")
            return False

    def play_segment(self, segment_idx):
        """Enhanced segment playback with completion check."""
        try:
            if segment_idx >= self.total_segments:
                return []

            # Only play if segment not completed
            if not self.is_segment_complete(segment_idx):
                self.current_segment = segment_idx
                words = self.get_segment_words(segment_idx)
                self._play_segment_audio()
                return words
            else:
                return self.temp_storage.get(segment_idx, {}).get('words', [])

        except Exception as e:
            logging.error(f"Error playing segment: {str(e)}")
            return []

    def _play_segment_audio(self):
        """Internal method to play current segment."""
        temp_file = None
        try:
            # Create temporary audio segment
            words_per_segment = 5
            start_pos = self.current_segment * words_per_segment
            end_pos = start_pos + words_per_segment

            # Find the corresponding time range in the audio
            if len(self.words) == 0:
                logging.error("No words recognized in file")
                return

            duration_per_word = len(self.audio_data) / len(self.words) / self.samplerate
            start_time = start_pos * duration_per_word
            end_time = end_pos * duration_per_word

            segment_audio = self.audio_data[int(start_time * self.samplerate):int(end_time * self.samplerate)]

            # Play using pygame
            temp_file = f'temp_segment_{int(time.time())}.wav'
            sf.write(temp_file, segment_audio, self.samplerate)

            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        finally:
            pygame.mixer.quit()
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logging.error(f"Failed to remove temp file: {str(e)}")

    def _recognize_words(self, file_path):
        """Recognizes words from audio file."""
        r = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                audio = r.record(source)
                text = r.recognize_google(audio, language="pl-PL")
                return text.split()
        except Exception as e:
            logging.error(f"Error recognizing words: {str(e)}")
            return []

    def replay_current_segment(self):
        """Powtarza odtwarzanie aktualnego segmentu."""
        if self.current_segment_audio is not None:
            try:
                self._play_segment_audio()
                return True
            except Exception as e:
                logging.error(f"Błąd podczas powtarzania segmentu: {str(e)}")
        return False

    def get_total_segments(self):
        """Zwraca całkowitą liczbę segmentów."""
        return self.total_segments

    def get_current_segment_words(self):
        """Returns words from current segment."""
        return self.segment_words_dict.get(self.current_segment, [])

    def get_segment_words(self, segment_idx):
        """Get words for a specific segment from matrix."""
        if 0 <= segment_idx < self.total_segments:
            return list(self.word_matrix[segment_idx])
        return []

    def mark_segment_complete(self, segment_idx, results):
        """Mark segment as complete and store results."""
        if segment_idx in self.segment_status:
            self.segment_status[segment_idx] = True
            self.temp_storage[segment_idx] = results
            return True
        return False

    def is_segment_complete(self, segment_idx):
        """Check if segment is completed."""
        return self.segment_status.get(segment_idx, False)

    def _update_current_segment_audio(self):
        """Updates the current segment audio data."""
        try:
            words_per_segment = 5
            start_pos = self.current_segment * words_per_segment
            end_pos = start_pos + words_per_segment

            # Find the corresponding time range in the audio
            if len(self.words) == 0:
                logging.error("No words recognized in file")
                return

            duration_per_word = len(self.audio_data) / len(self.words) / self.samplerate
            start_time = start_pos * duration_per_word
            end_time = end_pos * duration_per_word

            self.current_segment_audio = self.audio_data[int(start_time * self.samplerate):int(end_time * self.samplerate)]
        except Exception as e:
            logging.error(f"Error updating segment audio: {str(e)}")
            self.current_segment_audio = None

def zapisz_wynik(login, nazwa_audio, poprawne_słowa, powtórzone_słowa, słowa, folder_zapisu):
    """Zapisuje wyniki testu do pliku Excel."""
    try:
        os.makedirs(folder_zapisu, exist_ok=True)
        nazwa_pliku = os.path.join(folder_zapisu, f"{login}.xlsx")

        if os.path.exists(nazwa_pliku):
            df_existing = pd.read_excel(nazwa_pliku)
            numer_podejscia = df_existing.shape[0] + 1
        else:
            numer_podejscia = 1

        df_new = pd.DataFrame({
            "Numer podejścia": [numer_podejscia],
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

def powtorz_słowa(słowa, timeout=None):
    """Nagrywa i rozpoznaje powtórzone słowa użytkownika."""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            logging.info("Rozpoczęto nagrywanie")
            r.adjust_for_ambient_noise(source)
            # Explicitly set both timeout and phrase_time_limit to the same value
            audio = r.listen(source, timeout=timeout, phrase_time_limit=timeout)

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
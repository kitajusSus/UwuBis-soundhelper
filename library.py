import os
import pandas as pd
import soundfile as sf
import time
import logging
import numpy as np
import pygame
from vosk import Model, KaldiRecognizer
import wave
import json

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # Upewniamy się, że logi są w UTF-8
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

        # Ścieżka do modelu Vosk
        model_path = self.config.VOSK_MODEL_PATH
        if not os.path.exists(model_path):
            raise Exception(f"Model Vosk nie został znaleziony w ścieżce: {model_path}")
        self.vosk_model = Model(model_path)

    def load_audio_file(self, file_path):
        """Ładuje plik audio i dzieli go na segmenty na podstawie liczby słów."""
        try:
            # Ładowanie pliku audio
            self.audio_data, self.samplerate = sf.read(file_path)

            # Rozpoznawanie słów z audio
            self.words = self._recognize_words(file_path)
            if not self.words:
                logging.error("Nie rozpoznano żadnych słów w pliku")
                return False

            # Tworzenie segmentów na podstawie liczby słów
            words_per_segment = 5  # Upewnij się, że każdy segment ma dokładnie 5 słów
            self.segments = []
            self.segment_words_dict = {}

            for i in range(0, len(self.words), words_per_segment):
                segment_words = self.words[i:i + words_per_segment]
                if len(segment_words) == words_per_segment:
                    self.segment_words_dict[len(self.segments)] = segment_words
                    self.segments.append(i // words_per_segment)

            self.total_segments = len(self.segments)
            self.current_segment = 0

            # Aktualizacja bieżącego segmentu audio
            if self.total_segments > 0:
                self._update_current_segment_audio()

            logging.info(f"Utworzono {self.total_segments} segmentów po {words_per_segment} słów każdy")

            # Tworzenie macierzy słów (segmenty x 5 słów)
            total_possible_segments = len(self.words) // 5
            self.word_matrix = np.empty((total_possible_segments, 5), dtype=object)
            self.segment_status = {}
            self.segment_words_dict = {}

            segment_idx = 0
            for i in range(0, len(self.words), 5):
                segment_words = self.words[i:i+5]
                if len(segment_words) == 5:  # Tylko pełne segmenty
                    self.word_matrix[segment_idx] = segment_words
                    self.segment_words_dict[segment_idx] = segment_words
                    self.segment_status[segment_idx] = False  # Nieukończony
                    segment_idx += 1

            self.total_segments = segment_idx
            self.current_segment = 0

            # Aktualizacja bieżącego segmentu audio
            if self.total_segments > 0:
                self._update_current_segment_audio()

            return True

        except Exception as e:
            logging.error(f"Błąd podczas ładowania pliku audio '{file_path}': {str(e)}")
            return False

    def play_segment(self, segment_idx):
        """Odtwarza segment z możliwością sprawdzenia, czy został ukończony."""
        try:
            if (segment_idx >= self.total_segments):
                return []

            # Odtwarzaj tylko, jeśli segment nie został ukończony
            if not self.is_segment_complete(segment_idx):
                self.current_segment = segment_idx
                words = self.get_segment_words(segment_idx)
                self._play_segment_audio()
                return words
            else:
                return self.temp_storage.get(segment_idx, {}).get('words', [])

        except Exception as e:
            logging.error(f"Błąd podczas odtwarzania segmentu: {str(e)}")
            return []

    def _play_segment_audio(self):
        """Metoda wewnętrzna do odtwarzania bieżącego segmentu."""
        temp_file = None
        try:
            # Tworzenie tymczasowego segmentu audio
            words_per_segment = 5
            start_pos = self.current_segment * words_per_segment
            end_pos = start_pos + words_per_segment

            # Znalezienie odpowiedniego zakresu czasu w audio
            if len(self.words) == 0:
                logging.error("Nie rozpoznano żadnych słów w pliku")
                return

            duration_per_word = len(self.audio_data) / len(self.words) / self.samplerate
            start_time = start_pos * duration_per_word
            end_time = end_pos * duration_per_word

            segment_audio = self.audio_data[int(start_time * self.samplerate):int(end_time * self.samplerate)]

            # Odtwarzanie za pomocą pygame
            temp_file = f'temp_segment_{int(time.time())}.wav'
            sf.write(temp_file, segment_audio, self.samplerate)

            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        except Exception as e:
            logging.error(f"Błąd podczas odtwarzania segmentu audio: {str(e)}")
        finally:
            pygame.mixer.quit()
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logging.error(f"Nie udało się usunąć pliku tymczasowego: {str(e)}")

    def _recognize_words(self, file_path):
        """Rozpoznaje słowa z pliku audio za pomocą Vosk."""
        try:
            wf = wave.open(file_path, "rb")
            if wf.getnchannels() != 1:
                logging.info("Konwersja pliku audio do mono")
                # Konwersja do mono
                data, samplerate = sf.read(file_path)
                data_mono = data.mean(axis=1)
                temp_mono_file = "temp_mono.wav"
                sf.write(temp_mono_file, data_mono, samplerate)
                wf = wave.open(temp_mono_file, "rb")
            else:
                temp_mono_file = None

            rec = KaldiRecognizer(self.vosk_model, wf.getframerate())
            rec.SetWords(True)
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    results.append(res.get('text', ''))
            res = json.loads(rec.FinalResult())
            results.append(res.get('text', ''))
            text = ' '.join(results)
            logging.info(f"Rozpoznany tekst: {text}")
            words = text.strip().split()
            logging.info(f"Tokenizowane słowa: {words}")

            if temp_mono_file and os.path.exists(temp_mono_file):
                os.remove(temp_mono_file)

            return words
        except Exception as e:
            logging.error(f"Błąd podczas rozpoznawania słów: {str(e)}")
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
        """Zwraca słowa z bieżącego segmentu."""
        return self.segment_words_dict.get(self.current_segment, [])

    def get_segment_words(self, segment_idx):
        """Pobiera słowa dla konkretnego segmentu z macierzy."""
        if 0 <= segment_idx < self.total_segments:
            return list(self.word_matrix[segment_idx])
        return []

    def mark_segment_complete(self, segment_idx, results):
        """Oznacza segment jako ukończony i przechowuje wyniki."""
        if segment_idx in self.segment_status:
            self.segment_status[segment_idx] = True
            self.temp_storage[segment_idx] = results
            return True
        return False

    def is_segment_complete(self, segment_idx):
        """Sprawdza, czy segment został ukończony."""
        return self.segment_status.get(segment_idx, False)

    def _update_current_segment_audio(self):
        """Aktualizuje dane audio bieżącego segmentu."""
        try:
            words_per_segment = 5
            start_pos = self.current_segment * words_per_segment
            end_pos = start_pos + words_per_segment

            # Znalezienie odpowiedniego zakresu czasu w audio
            if len(self.words) == 0:
                logging.error("Nie rozpoznano żadnych słów w pliku")
                return

            duration_per_word = len(self.audio_data) / len(self.words) / self.samplerate
            start_time = start_pos * duration_per_word
            end_time = end_pos * duration_per_word

            self.current_segment_audio = self.audio_data[int(start_time * self.samplerate):int(end_time * self.samplerate)]
        except Exception as e:
            logging.error(f"Błąd podczas aktualizacji segmentu audio: {str(e)}")
            self.current_segment_audio = None

    def verify_user_audio(self, segment_idx, audio_file):
        """Weryfikuje nagranie użytkownika względem referencyjnego segmentu za pomocą Vosk."""
        try:
            wf = wave.open(audio_file, "rb")
            if wf.getnchannels() != 1 or wf.getframerate() != 16000:
                logging.info("Konwersja nagrania użytkownika do mono i 16000 Hz")
                # Konwersja do odpowiedniego formatu
                data, samplerate = sf.read(audio_file)
                # Jeśli jest stereo, zredukuj do mono
                if len(data.shape) > 1:
                    data = data.mean(axis=1)
                # Zmień częstotliwość próbkowania, jeśli to konieczne
                if samplerate != 16000:
                    import librosa
                    data = librosa.resample(data, orig_sr=samplerate, target_sr=16000)
                temp_formatted_file = "temp_user_formatted.wav"
                sf.write(temp_formatted_file, data, 16000)
                wf = wave.open(temp_formatted_file, "rb")
            else:
                temp_formatted_file = None

            rec = KaldiRecognizer(self.vosk_model, wf.getframerate())
            rec.SetWords(True)
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    results.append(res.get('text', ''))
            res = json.loads(rec.FinalResult())
            results.append(res.get('text', ''))
            user_text = ' '.join(results)
            logging.info(f"Rozpoznany tekst użytkownika: {user_text}")
            user_words = user_text.strip().split()

            if temp_formatted_file and os.path.exists(temp_formatted_file):
                os.remove(temp_formatted_file)

            # Pobranie słów referencyjnych dla tego segmentu
            reference_words = self.get_segment_words(segment_idx)
            reference_words = [word.lower() for word in reference_words]

            # Porównanie słów
            correct_words = [word for word in user_words if word.lower() in reference_words]
        
            # Obliczenie podobieństwa
            similarity = len(correct_words) / len(reference_words) if reference_words else 0

            logging.info(f"Słowa użytkownika: {user_words}, Słowa referencyjne: {reference_words}")
            logging.info(f"Wynik podobieństwa: {similarity}")

            return correct_words, similarity

        except Exception as e:
            logging.error(f"Błąd w verify_user_audio: {str(e)}")
            return [], 0.0
    
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

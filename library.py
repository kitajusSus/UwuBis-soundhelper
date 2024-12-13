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
    encoding='utf-8'
)

class AUDIOLIB:
    def __init__(self, config):
        self.config = config
        self.audio_data = None
        self.samplerate = None
        self.words = []
        self.timed_words = []  # (word, start, end)
        self.segment_status = {}
        self.temp_storage = {}

        model_path = self.config.VOSK_MODEL_PATH
        if not os.path.exists(model_path):
            raise Exception(f"Model Vosk nie został znaleziony w ścieżce: {model_path}")
        self.vosk_model = Model(model_path)

    def load_audio_file(self, file_path):
        try:
            self.audio_data, self.samplerate = sf.read(file_path)
            logging.info(f"Załadowano plik audio: {file_path}, samplerate: {self.samplerate}")

            self.timed_words = self._recognize_words_with_timing(file_path)
            self.words = [w[0] for w in self.timed_words]

            if not self.words:
                logging.error("Nie rozpoznano żadnych słów w pliku")
                return False

            return True

        except Exception as e:
            logging.error(f"Błąd podczas ładowania pliku audio '{file_path}': {str(e)}")
            return False

    def _recognize_words_with_timing(self, file_path):
        timed_words = []
        try:
            wf = wave.open(file_path, "rb")
            if wf.getnchannels() != 1:
                logging.info("Konwersja do mono")
                data, samplerate = sf.read(file_path)
                data_mono = data.mean(axis=1)
                temp_mono_file = "temp_mono.wav"
                sf.write(temp_mono_file, data_mono, samplerate)
                wf = wave.open(temp_mono_file, "rb")
            else:
                temp_mono_file = None

            rec = KaldiRecognizer(self.vosk_model, wf.getframerate())
            rec.SetWords(True)

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)

            result = json.loads(rec.FinalResult())
            if 'result' in result:
                for w in result['result']:
                    timed_words.append((w['word'], w['start'], w['end']))

            if temp_mono_file and os.path.exists(temp_mono_file):
                os.remove(temp_mono_file)
        except Exception as e:
            logging.error(f"Błąd podczas rozpoznawania słów z timingami: {str(e)}")

        return timed_words

    def extract_audio_for_words(self, selected_timed_words):
        # Tworzy fragment audio z podanych słów, 0.5 s ciszy na początku i końcu
        fs = self.samplerate
        audio_data = self.audio_data
        if not selected_timed_words:
            return np.array([], dtype=audio_data.dtype)
        total_duration = len(audio_data)/fs
        start_time = selected_timed_words[0][1] - 0.5
        end_time = selected_timed_words[-1][2] + 0.5
        start_time = max(0, start_time)
        end_time = min(end_time, total_duration)
        extracted = audio_data[int(start_time*fs):int(end_time*fs)]
        return extracted

    def verify_user_audio(self, audio_file):
        # Rozpoznaj słowa z pliku użytkownika za pomocą Vosk
        try:
            wf = wave.open(audio_file, "rb")
            if wf.getnchannels() != 1 or wf.getframerate() != 16000:
                logging.info("Konwersja nagrania użytkownika do mono i 16000 Hz")
                data, samplerate = sf.read(audio_file)
                if len(data.shape) > 1:
                    data = data.mean(axis=1)
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
                    r = json.loads(rec.Result())
                    results.append(r.get('text', ''))
            r = json.loads(rec.FinalResult())
            results.append(r.get('text', ''))
            user_text = ' '.join(results)
            logging.info(f"Rozpoznany tekst użytkownika: {user_text}")
            user_words = user_text.strip().split()

            if temp_formatted_file and os.path.exists(temp_formatted_file):
                os.remove(temp_formatted_file)
            return user_words
        except Exception as e:
            logging.error(f"Błąd w verify_user_audio: {str(e)}")
            return []

def zapisz_wynik(login, nazwa_audio, poprawne_słowa, powtórzone_słowa, słowa, folder_zapisu):
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
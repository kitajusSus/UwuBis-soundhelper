import os
import pandas as pd
import soundfile as sf
import time
import logging
import numpy as np
import json
import whisper
import torch
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget,
    QMessageBox, QFileDialog, QTextEdit, QSlider, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from PySide6.QtCore import QUrl

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

        # Wybór CPU lub GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Załadowanie modelu Whisper
        # Dostępne modele to m.in. "tiny", "base", "small", "medium", "large".
        # Upewnij się, że masz pobrane odpowiednie pliki modelu.
        self.whisper_model = whisper.load_model("base", device=device)

    def load_audio_file(self, file_path):
        """
        Ładuje plik audio do pamięci (soundfile) i rozpoznaje słowa przy użyciu Whisper.
        Zapisuje rozpoznane słowa w self.words i ich timingi w self.timed_words.
        """
        try:
            # Ładowanie samego pliku audio do tablicy numpy (jeśli potrzebne do dalszego przetwarzania)
            self.audio_data, self.samplerate = sf.read(file_path)
            logging.info(f"Załadowano plik audio: {file_path}, samplerate: {self.samplerate}")

            # Rozpoznawanie mowy z timingami słów
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
        """
        Rozpoznaje słowa z pliku audio za pomocą Whisper i zwraca listę krotek: (word, start, end).
        """
        timed_words = []
        try:
            # Transkrypcja z włączonymi timestampami słów
            result = self.whisper_model.transcribe(file_path, word_timestamps=True)

            # Każdy segment zawiera własną listę słów z polami "word", "start" i "end".
            for segment in result.get("segments", []):
                for w in segment.get("words", []):
                    timed_words.append((w["word"], w["start"], w["end"]))
        
        except Exception as e:
            logging.error(f"Błąd podczas rozpoznawania słów z timingami: {str(e)}")

        return timed_words

    def extract_audio_for_words(self, selected_timed_words):
        """
        Tworzy fragment audio zawierający wybrane słowa i dodaje 0.5 s ciszy przed i po fragmencie.
        Zwraca jako numpy array (wav w pamięci).
        """
        fs = self.samplerate
        audio_data = self.audio_data
        if not selected_timed_words:
            return np.array([], dtype=audio_data.dtype)

        total_duration = len(audio_data) / fs
        start_time = selected_timed_words[0][1] - 0.5
        end_time = selected_timed_words[-1][2] + 0.5
        start_time = max(0, start_time)
        end_time = min(end_time, total_duration)

        extracted = audio_data[int(start_time * fs) : int(end_time * fs)]
        return extracted
    def extract_audio_time_range(self, start_sec, end_sec):
        """
        Wycina z załadowanego pliku audio (self.audio_data) fragment od start_sec do end_sec (w sekundach).
        Zwraca tablicę numpy z tym fragmentem.
        """
        if self.audio_data is None or self.samplerate is None:
             return np.array([], dtype=np.float32)

        total_duration = len(self.audio_data) / self.samplerate
        start_sec = max(0, start_sec)
        end_sec = min(end_sec, total_duration)

        start_index = int(start_sec * self.samplerate)
        end_index = int(end_sec * self.samplerate)

    # Upewniamy się, że start_index <= end_index
        if end_index < start_index:
            end_index = start_index

        return self.audio_data[start_index:end_index]
    
    def verify_user_audio(self, audio_file):
        """
        Rozpoznaje słowa z pliku użytkownika za pomocą Whisper i zwraca listę słów
        (bez timingów). Możesz dopisać tu dodatkowe logiki (np. konwersję do mono).
        """
        try:
            # Transkrypcja użytkownika (bez timestampów, bo nie zawsze są potrzebne)
            result = self.whisper_model.transcribe(audio_file, word_timestamps=False)
            user_text = result.get("text", "")
            logging.info(f"Rozpoznany tekst użytkownika: {user_text}")

            user_words = user_text.strip().split()
            return user_words

        except Exception as e:
            logging.error(f"Błąd w verify_user_audio: {str(e)}")
            return []

def zapisz_wynik(login, nazwa_audio, poprawne_słowa, powtórzone_słowa, słowa, folder_zapisu):
    """
    Przykładowa funkcja zapisu wyników do pliku .xlsx (bez zmian).
    """
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


class YOUTUBESLIDER(QWidget):
    """
    Widget z QMediaPlayer + QSlider, umożliwiający:
    - Play, Pause, Stop
    - klikanie w suwak (seek)
    - gromadzenie informacji o faktycznie odtworzonych segmentach audio 
      (w milisekundach) w self.played_segments
    """
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # Inicjalizacja QMediaPlayer
        self.player = QMediaPlayer()
        # W nowszych wersjach PySide6 potrzebne jest QAudioOutput do odtwarzania dźwięku
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # Ustawiamy plik do odtwarzania
        self.player.setSource(QUrl.fromLocalFile(file_path))

        # Suwak postępu
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)  # 0-100% (przeskalowane do długości pliku)
        self.slider.setEnabled(False) # włączymy po poznaniu duration
        self.layout.addWidget(self.slider)

        # Etykieta z aktualnym czasem / całkowitym czasem
        self.time_label = QLabel("00:00 / 00:00")
        self.layout.addWidget(self.time_label)

        # Przyciski: Play, Stop
        btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")

        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)
        self.layout.addLayout(btn_layout)

        # Zmienne do rejestrowania odsłuchanych fragmentów
        self.last_position = 0      # ms
        self.played_segments = []   # [(segment_start_ms, segment_end_ms), ...]
        self.last_segment = None 
        # Połączenia sygnałów
        self.play_btn.clicked.connect(self.handlePlayPause)
        self.stop_btn.clicked.connect(self.handleStop)

        self.player.positionChanged.connect(self.onPositionChanged)
        self.player.durationChanged.connect(self.onDurationChanged)

        # Obsługa przesunięcia suwaka przez użytkownika (seek)
        self.slider.sliderReleased.connect(self.onSliderReleased)

    def onPositionChanged(self, position_ms: int):
        """
        Wywoływane przy zmianie pozycji odtwarzania (co klika/n milisekund).
        Aktualizuje suwak i etykietę czasu.
        """
        duration = self.player.duration()
        if duration > 0:
            slider_val = int(position_ms / duration * 100)
            self.slider.setValue(slider_val)

        # Aktualizacja etykiety czasu
        current_sec = position_ms // 1000
        duration_sec = duration // 1000
        self.time_label.setText(f"{self._format_time(current_sec)} / {self._format_time(duration_sec)}")

    def onDurationChanged(self, duration_ms: int):
        """
        Gdy załaduje się plik audio i znana jest jego długość.
        """
        if duration_ms > 0:
            self.slider.setEnabled(True)
            self.slider.setValue(0)

            # Zaktualizuj od razu etykietę
            current_sec = self.player.position() // 1000
            duration_sec = duration_ms // 1000
            self.time_label.setText(f"{self._format_time(current_sec)} / {self._format_time(duration_sec)}")

    def onSliderReleased(self):
        """
        Użytkownik przeciągnął suwak i puścił -> zmieniamy pozycję w pliku (seek).
        """
        duration = self.player.duration()
        if duration > 0:
            val = self.slider.value()
            new_pos_ms = int(val / 100 * duration)
            self.player.setPosition(new_pos_ms)

    def handlePlayPause(self):
        """
        Przykładowa metoda obsługi przycisku Play/Pause.
        """
        state = self.player.playbackState()
        if state != QMediaPlayer.PlayingState:
            # Start odtwarzania
            self.player.play()
            self.last_position = self.player.position()
        else:
            # Pauza -> zapisujemy odcinek [last_position, current]
            current_pos = self.player.position()
            if current_pos > self.last_position:
                # Zapisywaliśmy wszystkie segmenty:
                # self.played_segments.append((self.last_position, current_pos))

                # Teraz aktualizujemy TYLKO last_segment
                self.last_segment = (self.last_position, current_pos)

            self.last_position = current_pos
            self.player.pause()


    def handleStop(self):
        """
        Przykładowa metoda obsługi przycisku Stop.
        """
        current_pos = self.player.position()
        if current_pos > self.last_position:
            # self.played_segments.append((self.last_position, current_pos))
            self.last_segment = (self.last_position, current_pos)

        self.player.stop()
        self.player.setPosition(0)
        self.last_position = 0

    # --- NOWA METODA: getLastPlayedSegmentMs() ---
    def getLastPlayedSegmentMs(self):
        """
        Zwraca TYLKO ostatnio odsłuchany fragment (start_ms, end_ms),
        albo None, jeśli nic nie odsłuchano.
        """
        return self.last_segment

    def _format_time(self, seconds: int) -> str:
        """
        Zamiana liczby sekund na format mm:ss
        """
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def getPlayedSegmentsMs(self) -> list:
        """
        Zwraca listę (start_ms, end_ms) wszystkich faktycznie odsłuchanych fragmentów.
        """
        return self.played_segments



"""
    # Przykład onPositionChanged, by suwak był w milisekundach:
    def onPositionChanged(self, position_ms: int):
        
        #position_ms to aktualna pozycja odtwarzania w milisekundach.
        #Możesz ustawić slider tak, żeby miał range = duration w ms.
        
        if self.player.duration() > 0:
            duration_ms = self.player.duration()
            # Zakładamy, że self.slider.setRange(0, duration_ms) w onDurationChanged
            self.slider.setValue(position_ms)
        # ... aktualizuj ewentualnie label z czasem, etc.

    def onSliderReleased(self):
        
        #Gdy użytkownik puszcza suwak (w milisekundach).
        
        val = self.slider.value()  # to jest w ms
        self.player.setPosition(val)

    def onDurationChanged(self, duration_ms: int):
        
        #Kiedy znamy długość audio w milisekundach, ustawiamy zasięg suwaka.
        
        self.slider.setRange(0, duration_ms)
        self.slider.setValue(0)
"""

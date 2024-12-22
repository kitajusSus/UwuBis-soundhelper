import os
import sys
import time
import logging
import threading
import numpy as np
import soundfile as sf
import sounddevice as sd
import pygame
from thefuzz import fuzz
import string
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget,
    QMessageBox, QFileDialog, QTextEdit, QSlider, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# PLIKI ZEWNĘTRZNE (własne):
# - library.py zawiera: zapisz_wynik, AUDIOLIB, YOUTUBESLIDER
# - config.py zawiera klasę Config
from library import zapisz_wynik, AUDIOLIB, YOUTUBESLIDER
from config import Config

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


def style_button(btn: QPushButton):
    """Pomocnicza funkcja do stylowania przycisków."""
    btn.setStyleSheet("font-size:20px; padding:15px;")


class MainWindow(QMainWindow):
    """
    Główne okno aplikacji. 
    Zawiera logikę:
    - logowania użytkownika
    - wyboru folderu/pliku audio
    - trzech trybów ćwiczeń:
      * '5words' (segmenty po 5 słów)
      * 'slider' (ręczny wybór fragmentu w sekundach)
      * 'yt_slider' (odtwarzacz jak w YouTube, z dowolnym przewijaniem)
    - nagrywania wypowiedzi użytkownika
    - prezentacji wyników
    """

    # Sygnał emitowany po zakończeniu nagrywania (przekazujemy słowa użytkownika i słowa referencyjne)
    finishedRecording = Signal(list, list)

    def __init__(self):
        super().__init__()
        logging.info("Inicjalizacja okna głównego")

        # Konfiguracja i obiekty pomocnicze
        self.config = Config()
        self.audio_helper = AUDIOLIB(self.config)

        # Zmienne stanu
        self.login = ""
        self.folder_zapisu = self.config.RESULTS_FOLDER
        self.katalog_audio = self.config.AUDIO_FOLDER
        self.plik_audio = None
        self.auto_process = False  # Nieużywane w tym przykładzie, ale zostawione jako przykład

        # Tryby
        self.selection_mode = None  # "5words", "slider" lub "yt_slider"
        self.current_segment = 0
        self.total_segments = 0
        self.current_segment_words = []

        # Dla trybu „slider” (zakres w sekundach)
        self.slider_start_time = 0
        self.slider_end_time = 0
        # Kiedy kończymy nagrywać, pokazujemy wyniki
        self.finishedRecording.connect(self.showSegmentResults)
        # Dla trybu „yt_slider”
        self.yt_slider_widget = None

        self.reference_words = []  # Słowa referencyjne (z pliku)
        self.recording_time_left = 10
        self.recording_label = None
        self.record_timer = None

        # Podpinamy sygnał zakończenia nagrywania do metody wyświetlającej wyniki
        self.finishedRecording.connect(self.showSegmentResults)

        # Inicjalizacja UI
        self.setWindowTitle('UwuBiś')
        self.setGeometry(100, 100, 900, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.showLoginScreen()

    # ----------------------------------------------------------------------------
    # EKRAN LOGOWANIA
    # ----------------------------------------------------------------------------

    def showLoginScreen(self):
        self.clearLayout()
        login_label = QLabel("Login:")
        self.login_input = QLineEdit()

        login_button = QPushButton("Zaloguj się")
        style_button(login_button)
        login_button.clicked.connect(self.handleLogin)

        self.layout.addWidget(login_label)
        self.layout.addWidget(self.login_input)
        self.layout.addWidget(login_button)

    def handleLogin(self):
        self.login = self.login_input.text()
        if self.login.strip():
            self.showFolderSelection()
        else:
            QMessageBox.critical(self, "Błąd", "Wprowadź poprawny login")

    # ----------------------------------------------------------------------------
    # WYBÓR FOLDERU I PLIKÓW AUDIO
    # ----------------------------------------------------------------------------

    def showFolderSelection(self):
        self.clearLayout()

        self.auto_process_checkbox = QCheckBox("Automatycznie przetwarzaj wszystkie pliki audio (opcja niewykorzystana)")
        select_folder_btn = QPushButton("Wybierz folder z plikami audio")
        style_button(select_folder_btn)
        select_folder_btn.clicked.connect(self.selectAudioFolder)

        self.layout.addWidget(self.auto_process_checkbox)
        self.layout.addWidget(select_folder_btn)

    def selectAudioFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder z plikami audio")
        if folder:
            self.katalog_audio = folder
            self.auto_process = self.auto_process_checkbox.isChecked()
            self.showAudioFiles()

    def showAudioFiles(self):
        self.clearLayout()
        try:
            audio_files = [f for f in os.listdir(self.katalog_audio) if f.lower().endswith('.wav')]
            if not audio_files:
                QMessageBox.critical(self, "Błąd", "Brak plików audio w folderze")
                return

            self.file_list = QListWidget()
            self.file_list.addItems(audio_files)

            select_file_btn = QPushButton("Wybierz plik")
            style_button(select_file_btn)
            select_file_btn.clicked.connect(self.handleAudioFileSelection)

            back_btn = QPushButton("Cofnij")
            style_button(back_btn)
            back_btn.clicked.connect(self.showFolderSelection)

            self.layout.addWidget(self.file_list)
            self.layout.addWidget(select_file_btn)
            self.layout.addWidget(back_btn)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {e}")

    def handleAudioFileSelection(self):
        if not self.file_list.currentItem():
            QMessageBox.warning(self, "Uwaga", "Wybierz plik audio")
            return
        selected_file = self.file_list.currentItem().text()
        self.plik_audio = os.path.join(self.katalog_audio, selected_file)

        try:
            logging.info(f"Rozpoczęcie przetwarzania pliku audio: {self.plik_audio}")
            if not self.audio_helper.load_audio_file(self.plik_audio):
                raise ValueError("Nie udało się załadować pliku audio")
            self.chooseMainMode()
        except Exception as e:
            logging.error(f"Błąd: {str(e)}")
            QMessageBox.critical(self, "Błąd", f"Błąd podczas przetwarzania pliku audio:\n{str(e)}")

    # ----------------------------------------------------------------------------
    # WYBÓR TRYBU
    # ----------------------------------------------------------------------------

    def chooseMainMode(self):
        """
        Pozwala wybrać pomiędzy:
          - segmentami po 5 słów
          - trybem suwakowym (czas w sekundach)
          - trybem "YouTube slider" (dowolne przewijanie, rejestrowanie odsłuchanych fragmentów)
        """
        self.clearLayout()

        info_label = QLabel("Wybierz tryb ćwiczenia:")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        btn_layout = QHBoxLayout()

        # --- Tryb suwakowy prosty ---
        slider_mode_btn = QPushButton("Tryb suwakowy (w sekundach)")
        style_button(slider_mode_btn)
        slider_mode_btn.clicked.connect(self.setSliderMode)
        btn_layout.addWidget(slider_mode_btn)

        # --- Tryb 5words ---
        words5_mode_btn = QPushButton("Segmenty po 5 słów")
        style_button(words5_mode_btn)
        words5_mode_btn.clicked.connect(self.setFiveWordMode)
        btn_layout.addWidget(words5_mode_btn)

        # --- Tryb YouTube slider ---
        yt_slider_btn = QPushButton("Tryb YouTube Slider (dowolne przewijanie)")
        style_button(yt_slider_btn)
        yt_slider_btn.clicked.connect(self.setYouTubeSliderMode)
        btn_layout.addWidget(yt_slider_btn)

        self.layout.addLayout(btn_layout)

    # ----------------------------------------------------------------------------
    # TRYB "YOUTUBE SLIDER"
    # ----------------------------------------------------------------------------

    def setYouTubeSliderMode(self):
        self.selection_mode = "yt_slider"
        self.clearLayout()

        # Tutaj zakładamy, że plik_audio jest już wybrany
        if not self.plik_audio:
            QMessageBox.warning(self, "Błąd", "Nie wybrano pliku audio!")
            return

        # Inicjalizujemy nasz odtwarzacz w stylu YouTube
        self.yt_slider_widget = YOUTUBESLIDER(self.plik_audio)

        # Ustawiamy suwak co do milisekundy wewnątrz YOUTUBESLIDER:
        # np. w library.py YOUTUBESLIDER może mieć:
        #   slider.setRange(0, duration_ms)
        #   slider.valueChanged -> self.player.setPosition(new_val)
        #   ...
        # (Zakładamy, że to już zrobione w samej klasie)

        self.layout.addWidget(self.yt_slider_widget)

        # Przycisk do analizy TYLKO ostatniego segmentu
        recognize_btn = QPushButton("Rozpoznaj słowa z OSTATNIEGO odsłuchanego fragmentu")
        style_button(recognize_btn)
        recognize_btn.clicked.connect(self.recognizeYTLastSegment)
        self.layout.addWidget(recognize_btn)

        back_btn = QPushButton("Cofnij do wyboru trybu")
        style_button(back_btn)
        back_btn.clicked.connect(self.chooseMainMode)
        self.layout.addWidget(back_btn)

    def recognizeYTLastSegment(self):
        """
        1. Pobiera JEDYNIE ostatni segment odsłuchany (pauza -> stoper).
        2. Tworzy z niego np. temp plik .wav
        3. Wyznacza słowa referencyjne TYLKO z tego ostatniego segmentu
        4. Odtwarza i przechodzi do afterPlayingSelection()
        """
        if not self.yt_slider_widget:
            QMessageBox.warning(self, "Błąd", "Brak YOUTUBESLIDER")
            return

        # Metoda getLastPlayedSegmentMs() ZWRACA krotkę (start_ms, end_ms) OSTATNIEGO ODSŁUCHANEGO FRAGMENTU
        last_segment = self.yt_slider_widget.getLastPlayedSegmentMs()
        if not last_segment:
            QMessageBox.information(self, "Brak danych", "Nie odtworzono żadnego fragmentu.")
            return

        (start_ms, end_ms) = last_segment
        logging.info(f"Ostatni segment (ms): {start_ms} - {end_ms}")

        # Wycinamy tylko ten fragment
        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0

        segment_audio = self.audio_helper.extract_audio_time_range(start_sec, end_sec)
        if segment_audio.size == 0:
            QMessageBox.warning(self, "Błąd", "Fragment audio jest pusty.")
            return

        # Wyznaczamy słowa referencyjne TYLKO z tego fragmentu
        self.reference_words = []
        for (word, w_start, w_end) in self.audio_helper.timed_words:
            # Jesli [w_start, w_end] miesci sie w [start_sec, end_sec]
            if w_start >= start_sec and w_end <= end_sec:
                self.reference_words.append(word)

        # Odtwarzamy ten fragment
        self._play_audio_segment(segment_audio)

        # Przechodzimy do ekranu: nagraj swoją wypowiedź
        self.afterPlayingSelection()    
    # ----------------------------------------------------------------------------
        # TRYB SUWAKOWY (CZAS W SEKUNDACH)
    # ----------------------------------------------------------------------------

    def setSliderMode(self):
        self.selection_mode = "slider"
        self.startSliderMode()

    def startSliderMode(self):
        self.clearLayout()

        total_duration = len(self.audio_helper.audio_data) / self.audio_helper.samplerate

        info_label = QLabel(
            f"Tryb suwakowy - wybierz zakres w sekundach\n"
            f"(od 0 do {int(total_duration)}s, zaokrąglone w dół):"
        )
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setRange(0, int(total_duration))
        self.start_slider.setValue(0)
        self.start_slider.valueChanged.connect(self.update_range_label_time)

        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setRange(0, int(total_duration))
        self.end_slider.setValue(int(total_duration))
        self.end_slider.valueChanged.connect(self.update_range_label_time)

        sliders_layout = QHBoxLayout()
        sliders_layout.addWidget(QLabel("Początek (s):"))
        sliders_layout.addWidget(self.start_slider)
        sliders_layout.addWidget(QLabel("Koniec (s):"))
        sliders_layout.addWidget(self.end_slider)
        self.layout.addLayout(sliders_layout)

        self.range_label = QLabel("")
        self.range_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.range_label)

        self.update_range_label_time()

        confirm_btn = QPushButton("Zatwierdź zakres")
        style_button(confirm_btn)
        confirm_btn.clicked.connect(self.confirmSliderRange)
        self.layout.addWidget(confirm_btn)

        back_btn = QPushButton("Cofnij do wyboru trybu")
        style_button(back_btn)
        back_btn.clicked.connect(self.chooseMainMode)
        self.layout.addWidget(back_btn)

    def update_range_label_time(self):
        start_sec = self.start_slider.value()
        end_sec = self.end_slider.value()
        if end_sec < start_sec:
            end_sec = start_sec
        dur = end_sec - start_sec
        self.range_label.setText(f"Wybrany zakres: {start_sec}s - {end_sec}s (długość: {dur}s)")

    def confirmSliderRange(self):
        start_sec = self.start_slider.value()
        end_sec = self.end_slider.value()
        if end_sec < start_sec:
            end_sec = start_sec

        self.slider_start_time = start_sec
        self.slider_end_time = end_sec

        self.clearLayout()

        info_label = QLabel("Zakres czasu zatwierdzony. Odtwórz i nagraj swoją wypowiedź.")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        play_btn = QPushButton("Odtwórz wybrany fragment")
        style_button(play_btn)
        play_btn.clicked.connect(self.playSelectedTimeRange)
        self.layout.addWidget(play_btn)

        change_btn = QPushButton("Zmień zakres")
        style_button(change_btn)
        change_btn.clicked.connect(self.startSliderMode)
        self.layout.addWidget(change_btn)

    def playSelectedTimeRange(self):
        self.clearLayout()

        segment_audio = self.audio_helper.extract_audio_time_range(
            self.slider_start_time,
            self.slider_end_time
        )
        if segment_audio is None or len(segment_audio) == 0:
            QMessageBox.critical(self, "Błąd", "Nie udało się przygotować fragmentu audio.")
            return

        # Wyznaczamy słowa referencyjne (start_sec >= slider_start_time i end_sec <= slider_end_time)
        self.reference_words = []
        for (word, start_sec, end_sec) in self.audio_helper.timed_words:
            if start_sec >= self.slider_start_time and end_sec <= self.slider_end_time:
                self.reference_words.append(word)

        self._play_audio_segment(segment_audio)
        self.afterPlayingSelection()

    # ----------------------------------------------------------------------------
    # TRYB 5-SŁÓW (SEGMENTY)
    # ----------------------------------------------------------------------------

    def setFiveWordMode(self):
        self.selection_mode = "5words"
        self.current_segment = 0
        total_words = len(self.audio_helper.words)
        self.total_segments = total_words // 5 + (1 if total_words % 5 != 0 else 0)
        self.startSegmentTest()

    def startSegmentTest(self):
        if self.current_segment >= self.total_segments:
            QMessageBox.information(self, "Koniec", "Ukończono wszystkie segmenty!")
            self.showAudioFiles()  # powrót do wyboru plików
            return

        self.clearLayout()

        progress_label = QLabel(f"Segment {self.current_segment + 1} z {self.total_segments}")
        progress_label.setStyleSheet("font-size:20px; font-weight:bold;")
        progress_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(progress_label)

        start = self.current_segment * 5
        end = start + len(self.audio_helper.words[start:start + 5]) - 1
        self.current_segment_words = self.audio_helper.words[start:end + 1]

        word_label = QLabel(f"Słowa w tym segmencie: {len(self.current_segment_words)}")
        word_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(word_label)

        info_label = QLabel("Kliknij 'Rozpocznij segment' aby go odtworzyć.")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        start_btn = QPushButton("Rozpocznij segment")
        style_button(start_btn)
        start_btn.clicked.connect(self.playCurrentSegment_5words)
        self.layout.addWidget(start_btn)

    def playCurrentSegment_5words(self):
        self.clearLayout()
        start = self.current_segment * 5
        end = start + len(self.current_segment_words) - 1

        selected_timed_words = self.audio_helper.timed_words[start:end + 1]
        segment_audio = self.audio_helper.extract_audio_for_words(selected_timed_words)
        self.reference_words = [tw[0] for tw in selected_timed_words]

        self._play_audio_segment(segment_audio)
        self.afterPlayingSelection()

    # ----------------------------------------------------------------------------
    # PO ODTWORZENIU SŁÓW (obie ścieżki)
    # ----------------------------------------------------------------------------

    def afterPlayingSelection(self):
        self.clearLayout()
        """
        Ekran po odtworzeniu wybranego fragmentu. 
        Możliwość nagrania wypowiedzi, powtórzenia audio lub zmiany zakresu/segmentu.
        """
        instructions = QLabel("KLIKNIJ PRZYCISK I POWIEDZ TO, CO USŁYSZAŁEŚ")
        instructions.setStyleSheet("font-size:24px; font-weight:bold;")
        instructions.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(instructions)

        record_btn = QPushButton("Nagraj wymowę")
        style_button(record_btn)
        record_btn.clicked.connect(self.prepareRecording)
        self.layout.addWidget(record_btn)

        # Przycisk do ponownego odtworzenia ostatniego segmentu
        replay_btn = QPushButton("Powtórz ostatni segment")
        style_button(replay_btn)

        if self.selection_mode == "yt_slider":
            # Wracamy do recognizeYTLastSegment, aby ponownie odtworzyć 
            # (bo tam wytwarza i odtwarza temp fragment)
            replay_btn.clicked.connect(self.recognizeYTLastSegment)
        else:
            # stary mechanizm (5words/slider)
            replay_btn.clicked.connect(self.playCurrentSegment_5words)

        self.layout.addWidget(replay_btn)

        change_selection_btn = QPushButton("Zmień wybór słów/zakresu")
        style_button(change_selection_btn)

        if self.selection_mode == "yt_slider":
            change_selection_btn.clicked.connect(self.setYouTubeSliderMode)
        else:
            # inne tryby
            change_selection_btn.clicked.connect(self.startSegmentTest)

        self.layout.addWidget(change_selection_btn)

    def prepareRecording(self):
        """Ekran przed nagrywaniem, odliczanie itd."""
        self.clearLayout()
    
        info_label = QLabel("ZACZNIJ MÓWIĆ TO CO USŁYSZAŁEŚ WCZEŚNIEJ!")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        self.recording_time_left = 10
        self.recording_label = QLabel("")
        self.recording_label.setAlignment(Qt.AlignCenter)
        self.recording_label.setStyleSheet("font-size:20px;")
        self.layout.addWidget(self.recording_label)

        # Start nagrywania w osobnym wątku
        threading.Thread(target=self.record_audio, daemon=True).start()
    
        # Timer do aktualizacji odliczania
        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self.update_recording_countdown)
        self.record_timer.start(1000)
        self.update_recording_label()
    def update_recording_countdown(self):
        self.recording_time_left -= 1
        self.update_recording_label()
        if self.recording_time_left <= 0:
            self.record_timer.stop()

    def update_recording_label(self):
        self.recording_label.setText(f"Pozostało: {self.recording_time_left} s")

    def record_audio(self):
        """Faktyczne nagrywanie przy pomocy sounddevice."""
        duration = 10
        fs = 16000
        channels = 1
        temp_audio = "temp_user_audio.wav"

        logging.info("Rozpoczynam nagrywanie...")
        try:
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype='int16')
            sd.wait()
            sf.write(temp_audio, recording, fs)
            logging.info("Zakończono nagrywanie.")
        except Exception as e:
            logging.error(f"Błąd podczas nagrywania: {str(e)}")
            return

    # Transkrypcja usera
        user_words = self.audio_helper.verify_user_audio(temp_audio)

    # W momencie zakończenia nagrywania -> sygnał
        self.finishedRecording.emit(user_words, self.reference_words)

        # Usuwamy temp audio
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
    def normalize_word(self, word: str) -> str:
        word = word.strip(string.punctuation + " \t\n\r")
        word = word.lower()
        return word

    def are_words_similar(self,user_word: str, ref_word: str, threshold=80) -> bool:
        user_norm = self.normalize_word(user_word)
        ref_norm = self.normalize_word(ref_word)
        similarity = fuzz.ratio(user_norm, ref_norm)

        return similarity >= threshold 


    @Slot(list, list)
    def showSegmentResults(self, user_words, reference_words, is_replay=False):
        """
        Po nagraniu i rozpoznaniu wypowiedzi użytkownika – wyświetlamy wyniki.
        Zmieniamy tak, aby słowa referencyjne oryginalne były UKRYTE,
        dopóki użytkownik nie kliknie "Pokaż słowa referencyjne".
        """
        self.clearLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.layout.addWidget(self.results_text)

        # Podstawowe info
        if self.selection_mode == "yt_slider":
            self.results_text.append("Tryb YouTube Slider - Ostatni fragment\n")
        self.results_text.append(f"Liczba słów referencyjnych: {len(reference_words)}")

        
        # Wyliczamy poprawne słowa
        poprawne_słowa = []
        for w in user_words:
        # Jeżeli w jest podobne do któregokolwiek ref_word z progiem 80%,
        # uznajemy je za poprawne
            if any(self.are_words_similar(w, rw, 80) for rw in reference_words):
                poprawne_słowa.append(w)

        wynik = f"{len(poprawne_słowa)}/{len(reference_words)}"
        self.results_text.append(f"Wynik: {wynik}\n")

         # Wyświetlamy słowa użytkownika w kolejności (z informacją poprawne/nie)
        self.results_text.append("** Twoje słowa (w kolejności):")
        for w in user_words:
            if any(self.are_words_similar(w, rw, 80) for rw in reference_words):
                self.results_text.append(f"  ✓ {w}")
            else:
                self.results_text.append(f"  ✗ {w}")
        # Słowa referencyjne – NA RAZIE NIE POKAZUJEMY
        self.hidden_reference_words = reference_words  # Zapisujemy, by pokazać później

        # Przyciski na dole
        btn_layout = QHBoxLayout()

        # Przycisk „Pokaż słowa referencyjne”
        show_ref_btn = QPushButton("Pokaż słowa referencyjne")
        style_button(show_ref_btn)
        show_ref_btn.clicked.connect(self.showReferenceWords)
        btn_layout.addWidget(show_ref_btn)

        # ... plus reszta Twoich przycisków (powtórz, zmień wybór, zapisz_wynik etc.)
        # np.:
        self.layout.addWidget(self.results_text)
        back_btn = QPushButton("Zmień plik audio")
        style_button(back_btn)
        back_btn.clicked.connect(self.showAudioFiles)
        btn_layout.addWidget(back_btn)

        self.layout.addLayout(btn_layout)

        # Ewentualny zapis do Excel
        try:
            nazwa_pliku = os.path.basename(self.plik_audio) if self.plik_audio else "unknown.wav"
            zapisz_wynik(
                self.login,
                nazwa_pliku,
                poprawne_słowa,
                user_words,
                reference_words,
                self.config.RESULTS_FOLDER
            )
        except Exception as e:
            logging.error(f"Błąd zapisu wyników: {str(e)}")

    def showReferenceWords(self):
        """
        Po naciśnięciu przycisku „Pokaż słowa referencyjne” dopiero dodajemy je do QTextEdit.
        """
        self.results_text.append("\n** Słowa referencyjne (oryginalne):")
        for rw in self.hidden_reference_words:
            self.results_text.append(f"  {rw}")
    # ----------------------------------------------------------------------------
    # ODTWARZANIE FRAGMENTÓW AUDIO
    # ----------------------------------------------------------------------------

    def _play_audio_segment(self, segment_audio: np.ndarray):
        """
        Zapisuje fragment do pliku tymczasowego i odtwarza przy pomocy pygame.
        """
        temp_file = f'temp_segment_{int(time.time())}.wav'
        sf.write(temp_file, segment_audio, self.audio_helper.samplerate)
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                QApplication.processEvents()
                time.sleep(0.1)
        except Exception as e:
            logging.error(f"Błąd podczas odtwarzania audio: {str(e)}")
        finally:
            pygame.mixer.quit()
            if os.path.exists(temp_file):
                os.remove(temp_file)

    # ----------------------------------------------------------------------------
    # CZYSZCZENIE LAYOUTU
    # ----------------------------------------------------------------------------

    def clearLayout(self):
        """
        Usuwa wszystkie widgety z bieżącego layoutu, aby przejść do kolejnego ekranu/etapu.
        """
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clearLayoutHelper(item.layout())

    def clearLayoutHelper(self, layout):
        while layout.count() > 0:
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clearLayoutHelper(child.layout())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

import os
import sys
import time
import logging
import threading
import numpy as np
import soundfile as sf
import sounddevice as sd
import pygame
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QListWidget,
                               QMessageBox, QFileDialog, QTextEdit, QSlider, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from library import zapisz_wynik, AUDIOLIB
from config import Config



logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def style_button(btn):
    btn.setStyleSheet("font-size:20px; padding:15px;")

class MainWindow(QMainWindow):
    finishedRecording = Signal(list, list)  # user_words, reference_words

    def __init__(self):
        super().__init__()
        logging.info("Inicjalizacja okna głównego")

        self.config = Config()
        self.audio_helper = AUDIOLIB(self.config)

        self.login = ""
        self.folder_zapisu = self.config.RESULTS_FOLDER
        self.katalog_audio = self.config.AUDIO_FOLDER
        self.plik_audio = None
        self.auto_process = False

        self.selection_mode = None
        self.range_start_idx = 0
        self.range_end_idx = 0

        self.current_segment = 0
        self.total_segments = 0
        self.current_segment_words = []
        self.reference_words = []

        self.recording_time_left = 10
        self.recording_label = None
        self.record_timer = None

        self.finishedRecording.connect(self.showSegmentResults)

        self.setWindowTitle('UwuBiś')
        self.setGeometry(100, 100, 900, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.showLoginScreen()

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

    def showFolderSelection(self):
        self.clearLayout()
        self.auto_process_checkbox = QCheckBox("Automatycznie przetwarzaj wszystkie pliki audio")
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

    def chooseMainMode(self):
        self.clearLayout()
        info_label = QLabel("Wybierz tryb odsłuchu:")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        btn_layout = QHBoxLayout()

        range_mode_btn = QPushButton("Wybieranie suwakami z całego pliku")
        style_button(range_mode_btn)
        range_mode_btn.clicked.connect(self.setRangeMode)
        btn_layout.addWidget(range_mode_btn)

        words5_mode_btn = QPushButton("Segmenty po 5 słów")
        style_button(words5_mode_btn)
        words5_mode_btn.clicked.connect(self.setFiveWordMode)
        btn_layout.addWidget(words5_mode_btn)

        self.layout.addLayout(btn_layout)

    def setRangeMode(self):
        self.selection_mode = "range"
        self.startRangeMode()

    def startRangeMode(self):
        self.clearLayout()
        all_words = self.audio_helper.words
        if not all_words:
            QMessageBox.critical(self, "Błąd", "Brak słów w pliku.")
            self.showAudioFiles()
            return

        info_label = QLabel(f"Tryb cały plik: wybierz zakres słów (1 - {len(all_words)})")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setRange(0, len(all_words)-1)
        self.start_slider.setValue(0)
        self.start_slider.valueChanged.connect(self.update_range_label_global)

        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setRange(0, len(all_words)-1)
        self.end_slider.setValue(len(all_words)-1)
        self.end_slider.valueChanged.connect(self.update_range_label_global)

        sliders_layout = QHBoxLayout()
        sliders_layout.addWidget(QLabel("Początek:"))
        sliders_layout.addWidget(self.start_slider)
        sliders_layout.addWidget(QLabel("Koniec:"))
        sliders_layout.addWidget(self.end_slider)

        self.layout.addLayout(sliders_layout)

        self.range_label = QLabel("")
        self.range_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.range_label)

        self.update_range_label_global()

        confirm_btn = QPushButton("Zatwierdź zakres")
        style_button(confirm_btn)
        confirm_btn.clicked.connect(self.confirmGlobalRange)
        self.layout.addWidget(confirm_btn)

    def update_range_label_global(self):
        all_words = self.audio_helper.words
        start_idx = self.start_slider.value()
        end_idx = self.end_slider.value()
        if end_idx < start_idx:
            end_idx = start_idx
        count = end_idx - start_idx + 1
        self.range_label.setText(f"Wybrany zakres: od {start_idx+1} do {end_idx+1} (razem {count} słów)")

    def confirmGlobalRange(self):
        self.range_start_idx = self.start_slider.value()
        self.range_end_idx = self.end_slider.value()
        if self.range_end_idx < self.range_start_idx:
            self.range_end_idx = self.range_start_idx

        self.clearLayout()

        info_label = QLabel("Zakres słów z całego pliku zatwierdzony. Odtwórz je teraz.")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        play_btn = QPushButton("Odtwórz wybrany zakres")
        style_button(play_btn)
        play_btn.clicked.connect(self.playSelectedRangeGlobal)
        self.layout.addWidget(play_btn)

        change_btn = QPushButton("Zmień zakres")
        style_button(change_btn)
        change_btn.clicked.connect(self.startRangeMode)
        self.layout.addWidget(change_btn)

    def playSelectedRangeGlobal(self):
        self.clearLayout()
        # Tworzymy fragment audio z wybranego zakresu
        selected_timed_words = self.audio_helper.timed_words[self.range_start_idx:self.range_end_idx+1]
        segment_audio = self.audio_helper.extract_audio_for_words(selected_timed_words)
        if segment_audio is None or len(segment_audio) == 0:
            QMessageBox.critical(self, "Błąd", "Nie udało się przygotować fragmentu audio.")
            return

        self.reference_words = [tw[0] for tw in selected_timed_words]
        self._play_audio_segment(segment_audio)
        self.afterPlayingSelection()

    def setFiveWordMode(self):
        self.selection_mode = "5words"
        self.current_segment = 0
        # W trybie 5words korzystamy z podziału na segmenty
        self.total_segments = len(self.audio_helper.words)//5 + (1 if len(self.audio_helper.words)%5!=0 else 0)
        self.startSegmentTest()

    def startSegmentTest(self):
        if self.current_segment >= self.total_segments:
            QMessageBox.information(self, "Koniec", "Ukończono wszystkie segmenty!")
            self.showAudioFiles()
            return

        self.clearLayout()

        progress_label = QLabel(f"Segment {self.current_segment + 1} z {self.total_segments}")
        progress_label.setStyleSheet("font-size:20px; font-weight:bold;")
        progress_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(progress_label)

        start = self.current_segment*5
        end = start + len(self.audio_helper.words[start:start+5])-1
        self.current_segment_words = self.audio_helper.words[start:end+1]

        word_label = QLabel(f"Słowa w tym segmencie: {len(self.current_segment_words)}")
        word_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(word_label)

        info_label = QLabel("To jest segment 5-słowowy. Kliknij 'Rozpocznij segment' aby go odtworzyć.")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        start_btn = QPushButton("Rozpocznij segment")
        style_button(start_btn)
        start_btn.clicked.connect(self.playCurrentSegment_5words)
        self.layout.addWidget(start_btn)

    def playCurrentSegment_5words(self):
        self.clearLayout()
        # wyodrębnienie segmentu 5 słów z timed_words
        start = self.current_segment*5
        end = start + len(self.current_segment_words)-1
        selected_timed_words = self.audio_helper.timed_words[start:end+1]
        segment_audio = self.audio_helper.extract_audio_for_words(selected_timed_words)
        self.reference_words = [tw[0] for tw in selected_timed_words]
        self._play_audio_segment(segment_audio)
        self.afterPlayingSelection()

    def afterPlayingSelection(self):
        self.clearLayout()
        instructions = QLabel("KLIKNIJ PRZYCISK I POWIEDZ CO USŁYSZAŁEŚ")
        instructions.setStyleSheet("font-size:24px; font-weight:bold;")
        instructions.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(instructions)

        record_btn = QPushButton("Nagraj wymowę")
        style_button(record_btn)
        record_btn.clicked.connect(self.prepareRecording)
        self.layout.addWidget(record_btn)

        replay_btn = QPushButton("Powtórz odtwarzanie słów")
        style_button(replay_btn)
        if self.selection_mode == "range":
            replay_btn.clicked.connect(self.playSelectedRangeGlobal)
        else:
            replay_btn.clicked.connect(self.playCurrentSegment_5words)
        self.layout.addWidget(replay_btn)

        change_selection_btn = QPushButton("Zmień wybór słów/zakresu")
        style_button(change_selection_btn)
        if self.selection_mode == "range":
            change_selection_btn.clicked.connect(self.startRangeMode)
        else:
            change_selection_btn.clicked.connect(self.startSegmentTest)
        self.layout.addWidget(change_selection_btn)

    def prepareRecording(self):
        self.clearLayout()
        info_label = QLabel("Nagrywanie zaraz się rozpocznie.")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)

        self.recording_time_left = 10
        self.recording_label = QLabel("")
        self.recording_label.setAlignment(Qt.AlignCenter)
        self.recording_label.setStyleSheet("font-size:20px;")
        self.layout.addWidget(self.recording_label)

        threading.Thread(target=self.record_audio, daemon=True).start()
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
        duration = 10  # Czas nagrywania w sekundach
        fs = 16000  #wymagane przez ten vosk model wiec nie zmieniac bo nie testowałem z innymi
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

        user_words = self.audio_helper.verify_user_audio(temp_audio)
        # Emitujemy sygnał aby pokazać wyniki
        self.finishedRecording.emit(user_words, self.reference_words)
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
       
    @Slot(list, list)
    def showSegmentResults(self, user_words, reference_words, is_replay=False):
        self.clearLayout()
        results_text = QTextEdit()
        results_text.setReadOnly(True)
        wynik = f"{len([w for w in user_words if w.lower() in [rw.lower() for rw in reference_words]])}/{len(reference_words)}"

        if self.selection_mode == "range":
            segment_info = f"Zakres słów {self.range_start_idx+1} - {self.range_end_idx+1} z {len(self.audio_helper.words)}"
        else:
            segment_info = f"Segment {self.current_segment + 1} z {self.total_segments}"

        attempt_info = " (Powtórka)" if is_replay else ""

        results_text.append(f"{segment_info}{attempt_info}\n")
        results_text.append(f"Wynik: {wynik}\n")

        results_text.append("\nTwoje odpowiedzi:\n")
        reference_words_lower = [rw.lower() for rw in reference_words]
        for w in reference_words:
            if w.lower() in [uw.lower() for uw in user_words]:
                results_text.append(f"✓ {w} (prawidłowe)\n")
            else:
                results_text.append(f"✗ {w} (ŹLE POWIEDZIANE)\n")

        self.layout.addWidget(results_text)

        show_all_words_btn = QPushButton("Pokaż słowa, które trzeba było powiedzieć")
        style_button(show_all_words_btn)
        show_all_words_btn.clicked.connect(lambda: self.showAllWords(reference_words))
        self.layout.addWidget(show_all_words_btn)

        btn_layout = QHBoxLayout()

        replay_btn = QPushButton("Powtórz odtwarzanie słów")
        style_button(replay_btn)
        if self.selection_mode == "range":
            replay_btn.clicked.connect(self.playSelectedRangeGlobal)
        else:
            replay_btn.clicked.connect(self.playCurrentSegment_5words)
        btn_layout.addWidget(replay_btn)

        change_selection_btn = QPushButton("Zmień wybór")
        style_button(change_selection_btn)
        if self.selection_mode == "range":
            change_selection_btn.clicked.connect(self.startRangeMode)
        else:
            change_selection_btn.clicked.connect(self.startSegmentTest)
        btn_layout.addWidget(change_selection_btn)

        if self.selection_mode == "5words" and self.current_segment + 1 < self.total_segments:
            next_btn = QPushButton("Następny segment")
            style_button(next_btn)
            next_btn.clicked.connect(self.nextSegment)
            btn_layout.addWidget(next_btn)

        finish_btn = QPushButton("Zakończ ćwiczenie")
        style_button(finish_btn)
        finish_btn.clicked.connect(self.showAudioFiles)
        btn_layout.addWidget(finish_btn)

        self.layout.addLayout(btn_layout)
         
        try:
            logging.info(f"{segment_info} - Słowa referencyjne: {', '.join(reference_words)}")
            logging.info(f"{segment_info} - Słowa użytkownika: {', '.join(user_words)}")
        except Exception as e:
            logging.error(f"Błąd podczas logowania słów: {str(e)}")


        nazwa_pliku = os.path.basename(self.plik_audio)
        poprawne_słowa = [w for w in user_words if w.lower() in reference_words_lower]
        zapisz_wynik(self.login, f"{nazwa_pliku}", poprawne_słowa, user_words, reference_words, self.config.RESULTS_FOLDER)

    def showAllWords(self, current_words):
        count = self.layout.count()
        bottom_buttons_index = -1
        for i in reversed(range(count)):
            item = self.layout.itemAt(i)
            if item and item.layout():
                bottom_buttons_index = i
                break

        words_widget = QWidget()
        words_widget.setMaximumHeight(100)
        words_layout = QHBoxLayout(words_widget)
        words_layout.setContentsMargins(10,10,10,10)
        words_layout.setSpacing(10)

        for w in current_words:
            word_btn = QPushButton(w)
            word_btn.setStyleSheet("""
                font-size:20px;
                padding:5px 10px;
                background-color: green;
                color: white;
                border-radius:5px;
                text-align: left;
            """)
            words_layout.addWidget(word_btn)

        if bottom_buttons_index >= 0:
            self.layout.insertWidget(bottom_buttons_index, words_widget)
        else:
            self.layout.addWidget(words_widget)

    def _play_audio_segment(self, segment_audio):
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

    def nextSegment(self):
        self.current_segment += 1
        self.startSegmentTest()

    def clearLayout(self):
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


    

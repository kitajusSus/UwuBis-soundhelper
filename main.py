import os
import sys
import time
import speech_recognition as sr 
import logging
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QListWidget,
                               QMessageBox, QFileDialog, QTextEdit, QCheckBox)
from PySide6.QtCore import Qt, QTimer
from library import zapisz_wynik, AUDIOLIB
from config import Config  # Upewnij się, że m asz plik config.py z klasą Config
import spacy  # Importujemy spaCy
#nie działa github

# Ładujemy model języka polskiego
nlp = spacy.load('pl_core_news_sm')

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        logging.info("Inicjalizacja okna głównego")

        # Inicjalizacja zmiennych
        self.recognizer = sr.Recognizer()
        self.sr = sr
        self.config = Config()
        self.audio_helper = AUDIOLIB(self.config)
        self.current_segment = 0
        self.total_segments = 0
        self.current_segment_words = []
        self.login = ""
        self.folder_zapisu = self.config.RESULTS_FOLDER
        self.katalog_audio = self.config.AUDIO_FOLDER
        self.plik_audio = None
        self.auto_process = False

        # Inicjalizacja interfejsu
        self.initUI()

    def initUI(self):
        self.setWindowTitle('UwuBiś')
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.showLoginScreen()

    def showLoginScreen(self):
        self.clearLayout()

        login_label = QLabel("Login:")
        self.login_input = QLineEdit()
        login_button = QPushButton("Zaloguj się")
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
            audio_files = [f for f in os.listdir(self.katalog_audio) if f.endswith('.wav')]
            if not audio_files:
                QMessageBox.critical(self, "Błąd", "Brak plików audio w folderze")
                return

            self.file_list = QListWidget()
            self.file_list.addItems(audio_files)
            select_file_btn = QPushButton("Wybierz plik")
            select_file_btn.clicked.connect(self.handleAudioFileSelection)
            back_btn = QPushButton("Cofnij")
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

            self.current_segment = 0
            self.total_segments = self.audio_helper.total_segments

            if self.total_segments == 0:
                raise ValueError("Nie utworzono żadnych segmentów z pliku audio")

            self.startSegmentTest()

        except Exception as e:
            logging.error(f"Błąd podczas przetwarzania pliku audio: {str(e)}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas przetwarzania pliku audio:\n{str(e)}")

    def startSegmentTest(self):
        """Rozpoczyna test dla aktualnego segmentu."""
        if self.current_segment >= self.total_segments:
            QMessageBox.information(self, "Koniec", "Ukończono wszystkie segmenty!")
            self.showAudioFiles()
            return

        self.clearLayout()

        # Wyświetlenie postępu segmentów
        progress_label = QLabel(f"Segment {self.current_segment + 1} z {self.total_segments}")
        progress_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        progress_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(progress_label)

        # Wyświetlenie liczby słów
        words = self.audio_helper.get_segment_words(self.current_segment)
        self.current_segment_words = words
        word_label = QLabel(f"Słowa w tym segmencie: {len(words)}")
        word_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(word_label)

        # Dodanie przycisku start
        start_btn = QPushButton("Rozpocznij segment")
        start_btn.clicked.connect(self.playCurrentSegment)
        self.layout.addWidget(start_btn)

    def playCurrentSegment(self):
        try:
            self.clearLayout()

            # Odtwarzanie bieżącego segmentu
            words = self.audio_helper.play_segment(self.current_segment)
            self.current_segment_words = words

            # Wyświetlenie komunikatu
            speak_label = QLabel("Powtórz słowa...")
            self.layout.addWidget(speak_label)

            # Dodanie przycisku do potwierdzenia
            confirm_btn = QPushButton("WCISNIJ BY ZACZAC MÓWIĆ")
            confirm_btn.clicked.connect(self.confirmRepetition)
            self.layout.addWidget(confirm_btn)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {e}")

    def confirmRepetition(self):
        temp_audio = "temp_user_audio.wav"
        try:
            # Nagrywanie dźwięku za pomocą sounddevice
            import sounddevice as sd
            import soundfile as sf
            duration = 10  # czas nagrywania w sekundach
            fs = 16000     # częstotliwość próbkowania
            channels = 1   # liczba kanałów (mono)
            logging.info("Rozpoczynam nagrywanie...")
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype='int16')
            sd.wait()  # Oczekiwanie na zakończenie nagrywania
            sf.write(temp_audio, recording, fs)
            logging.info("Zakończono nagrywanie.")

            # Weryfikacja wymowy za pomocą Vosk
            words, similarity = self.audio_helper.verify_user_audio(
                self.current_segment,
                temp_audio
            )

            self.showSegmentResults(words)

        except Exception as e:
            logging.error(f"Błąd podczas nagrywania: {str(e)}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas nagrywania: {str(e)}")
        finally:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)     


    def showSegmentResults(self, repeated_words, is_replay=False):
        self.clearLayout()

        # Wyświetlenie wyników
        results_text = QTextEdit()
        results_text.setReadOnly(True)
        current_words = self.current_segment_words
        wynik = f"{len(repeated_words)}/{len(current_words)}"

        # Informacje o próbie i postępie
        segment_info = f"Segment {self.current_segment + 1} z {self.total_segments}"
        attempt_info = " (Powtórka)" if is_replay else ""

        results_text.append(f"{segment_info}{attempt_info}\n")
        results_text.append(f"Wynik: {wynik}\n")

        # Wyświetlenie odpowiedzi użytkownika
        results_text.append("\nTwoje odpowiedzi:\n")
        for word in repeated_words:
            if word in current_words:
                results_text.append(f"✓ {word} (prawidłowe)\n")
            else:
                results_text.append(f"✗ {word} (nieprawidłowe)\n")

        self.layout.addWidget(results_text)

        # Dodanie przycisku do pokazania słów referencyjnych
        show_words_btn = QPushButton("Pokaż słowa do powtórzenia")
        show_words_btn.clicked.connect(lambda: self.showReferenceWords(results_text, current_words, repeated_words, show_words_btn))
        self.layout.addWidget(show_words_btn)

        # Przyciski nawigacyjne
        btn_layout = QHBoxLayout()

        replay_btn = QPushButton("Powtórz ten segment")
        replay_btn.clicked.connect(self.replayCurrentSegment)
        btn_layout.addWidget(replay_btn)

        if self.current_segment + 1 < self.total_segments:
            next_btn = QPushButton("Następny segment")
            next_btn.clicked.connect(self.nextSegment)
            btn_layout.addWidget(next_btn)

        finish_btn = QPushButton("Zakończ ćwiczenie")
        finish_btn.clicked.connect(self.showAudioFiles)
        btn_layout.addWidget(finish_btn)

        self.layout.addLayout(btn_layout)

        # Zapisanie wyników
        nazwa_pliku = os.path.basename(self.plik_audio)
        attempt_suffix = "_retry" if is_replay else ""
        zapisz_wynik(self.login,
                     f"{nazwa_pliku}_segment_{self.current_segment + 1}{attempt_suffix}",
                     repeated_words, repeated_words,
                     current_words, self.folder_zapisu)

    def showReferenceWords(self, results_text, current_words, repeated_words, button):
        results_text.append("\nSłowa do powtórzenia:\n")
        for word in current_words:
            if word in repeated_words:
                results_text.append(f"✓ {word} (poprawnie powiedziane)\n")
            else:
                results_text.append(f"✗ {word} (ŹLE POWIEDZIANE)\n")
        button.setEnabled(False)

    def replayCurrentSegment(self):
        self.playCurrentSegment()

    def nextSegment(self):
        self.current_segment += 1
        self.startSegmentTest()

    def clearLayout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clearLayoutHelper(item.layout())

    def clearLayoutHelper(self, layout):
        while layout.count():
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


# DZIENNIK POKŁADOWY
## 03.12.2024
"""
taka sciana tekstu byle tylko wybombiło ten program gdy akurat NAPRAWIŁEM WSZYSTKIE BLEDY ALE TERAZ NAGLE STWIERDZA ZE NIE WIDZI NICZEGO I NIE WLACZY AUDIO
"""

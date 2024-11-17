import os
import sys
import time
import datetime
import threading
import logging
import soundfile as sf
import unicodedata
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QLineEdit, QListWidget, 
                            QMessageBox, QFileDialog, QTextEdit)
from PySide6.QtCore import Qt, QTimer, QTime
from library import zapisz_wynik, rozpoznaj_slowa_z_pliku, powtorz_słowa, odtwarzaj_audio
import pygame  
from library import AUDIOLIB



class Config:
    DEFAULT_SEGMENT_DURATION = 5
    WORDS_PER_CHAPTER = 5
    RESULTS_FOLDER = "wyniki/"
    AUDIO_FOLDER = "audio/demony/"
    SPEAKING_TIME = 10  # Stały czas na odpowiedź - nie zmieniać

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Window initialization started")
        
        # Initialize variables first
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.countdown)
        self.countdown_timer.setInterval(1000)
        self.time_remaining = 0
        self.time_label = None
        self.is_timer_active = False
        
        # Initialize other attributes
        self.config = Config()
        self.audio_helper = AUDIOLIB(self.config)
        self.current_segment = 0
        self.total_segments = 0
        
        # Initialize variables from config
        self.login = ""
        self.folder_zapisu = self.config.RESULTS_FOLDER
        self.katalog_audio = self.config.AUDIO_FOLDER
        self.plik_audio = None
        
        # Setup UI last
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
        if self.login == "test":  # Przykładowy login
            self.showFolderSelection()
        else:
            QMessageBox.critical(self, "Błąd", "Niepoprawny login")
            
    def showFolderSelection(self):
        self.clearLayout()
        select_folder_btn = QPushButton("Wybierz folder z plikami audio")
        select_folder_btn.clicked.connect(self.selectAudioFolder)
        self.layout.addWidget(select_folder_btn)
        
    def selectAudioFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder z plikami audio")
        if folder:
            self.katalog_audio = folder
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
        
        if self.audio_helper.load_audio_file(self.plik_audio):
            self.current_segment = 0
            self.total_segments = self.audio_helper.get_total_segments()
            self.startSegmentTest()
        else:
            QMessageBox.critical(self, "Błąd", "Nie udało się załadować pliku audio")

    def startSegmentTest(self):
        """Rozpoczyna test dla aktualnego segmentu."""
        if self.current_segment >= self.total_segments:
            QMessageBox.information(self, "Koniec", "Ukończono wszystkie segmenty!")
            self.showAudioFiles()
            return
            
        self.clearLayout()
        
        # Show segment progress
        progress_label = QLabel(f"Segment {self.current_segment + 1} z {self.total_segments}")
        progress_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        progress_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(progress_label)
        
        # Show word count
        words = self.audio_helper.get_current_segment_words()
        word_label = QLabel(f"Słowa w tym segmencie: {len(words)}")
        word_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(word_label)
        
        # Add start button
        start_btn = QPushButton("Rozpocznij segment")
        start_btn.clicked.connect(self.playCurrentSegment)
        self.layout.addWidget(start_btn)

    def countdown(self):
        """Aktualizuje wyświetlany czas pozostały."""
        if not self.is_timer_active or not self.time_label:
            self.countdown_timer.stop()
            return
            
        if self.time_remaining >= 0:
            try:
                self.time_label.setText(f"Pozostało: {self.time_remaining} sekund")
                self.time_remaining -= 1
                QApplication.processEvents()
            except RuntimeError:
                self.countdown_timer.stop()
                self.is_timer_active = False
        else:
            self.countdown_timer.stop()
            self.is_timer_active = False
            if self.time_label:
                try:
                    self.time_label.setText("CZAS MINĄŁ!")
                    self.time_label.setStyleSheet("QLabel { color: #ff0000; font-size: 24px; font-weight: bold; }")
                except RuntimeError:
                    pass

    def playCurrentSegment(self):
        try:
            self.clearLayout()
            
            # Show progress and instructions
            progress_label = QLabel(f"Segment {self.current_segment + 1} z {self.total_segments}")
            progress_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
            self.layout.addWidget(progress_label)
            
            listening_label = QLabel("Słuchaj uważnie następnych 5 słów...")
            self.layout.addWidget(listening_label)
            
            QApplication.processEvents()
            
            # Play current 5-word segment
            current_words = self.audio_helper.play_segment(self.current_segment, self.plik_audio)
            if not current_words:
                raise Exception("Nie udało się odtworzyć segmentu")
            
            # Show 'speak now' message with timer
            self.clearLayout()
            
            self.speak_label = QLabel("TERAZ MOŻESZ MÓWIĆ!")
            self.speak_label.setStyleSheet("QLabel { color: red; font-size: 24px; font-weight: bold; }")
            self.speak_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.speak_label)

            # Dodaj label do wyświetlania czasu
            self.time_label = QLabel()
            self.time_label.setStyleSheet("QLabel { font-size: 18px; }")
            self.time_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.time_label)

            # Initialize timer
            self.time_remaining = self.config.SPEAKING_TIME
            self.time_label.setText(f"Pozostało: {self.time_remaining} sekund")
            
            # Start timer and recording
            results_ready = False
            poprawne_slowa = []
            powtórzone_słowa = []
            
            def handle_recording():
                nonlocal results_ready, poprawne_slowa, powtórzone_słowa
                poprawne_slowa, powtórzone_słowa = powtorz_słowa(current_words, timeout=10.0)
                results_ready = True
            
            recording_thread = threading.Thread(target=handle_recording)
            recording_thread.daemon = True
            recording_thread.start()
            
            # Wait for recording while keeping timer running
            start_time = time.time()
            end_time = start_time + 10.0  # Full 10 seconds duration
            
            while time.time() < end_time and not results_ready:
                current_time = time.time()
                remaining = end_time - current_time
                
                # Update timer display
                self.time_remaining = max(0, int(remaining))
                if self.time_label:
                    self.time_label.setText(f"Pozostało: {self.time_remaining} sekund")
                
                # Process events and short sleep
                QApplication.processEvents()
                time.sleep(0.1)

            # Ensure we stop everything properly
            self.countdown_timer.stop()
            self.is_timer_active = False
            if recording_thread.is_alive():
                recording_thread.join(timeout=1.0)
                
            self.showSegmentResults(poprawne_slowa, powtórzone_słowa)

        except Exception as e:
            self.is_timer_active = False
            self.countdown_timer.stop()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas testu: {e}")

    def replayCurrentSegment(self):
        try:
            self.clearLayout()
            
            # Show replay message
            replay_label = QLabel("Powtórka segmentu - spróbuj jeszcze raz!")
            replay_label.setStyleSheet("QLabel { color: blue; font-size: 18px; }")
            replay_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(replay_label)
            
            QApplication.processEvents()
            
            # Play audio again
            current_words = self.audio_helper.get_current_segment_words()
            if not self.audio_helper.replay_current_segment():
                raise Exception("Nie można powtórzyć segmentu")
                
            # Show speak message
            self.clearLayout()
            speak_label = QLabel("TERAZ MOŻESZ MÓWIĆ!")
            speak_label.setStyleSheet("QLabel { color: red; font-size: 24px; font-weight: bold; }")
            speak_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(speak_label)
            
            # Add timer label
            self.time_label = QLabel()
            self.time_label.setStyleSheet("QLabel { font-size: 18px; }")
            self.time_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.time_label)

            # Reset and start timer
            self.time_remaining = self.config.SPEAKING_TIME
            
            # Get new attempt
            results_ready = False
            poprawne_slowa = []
            powtórzone_słowa = []
            
            def handle_recording():
                nonlocal results_ready, poprawne_slowa, powtórzone_słowa
                poprawne_slowa, powtórzone_słowa = powtorz_słowa(current_words, timeout=10.0)
                results_ready = True
            
            recording_thread = threading.Thread(target=handle_recording)
            recording_thread.daemon = True
            recording_thread.start()
            
            # Wait for recording while keeping timer running
            start_time = time.time()
            end_time = start_time + 10.0  # Full 10 seconds duration
            
            while time.time() < end_time and not results_ready:
                current_time = time.time()
                remaining = end_time - current_time
                
                # Update timer display
                self.time_remaining = max(0, int(remaining))
                if self.time_label:
                    self.time_label.setText(f"Pozostało: {self.time_remaining} sekund")
                
                # Process events and short sleep
                QApplication.processEvents()
                time.sleep(0.1)
            
            # Ensure we stop everything properly
            self.countdown_timer.stop()
            self.is_timer_active = False
            if recording_thread.is_alive():
                recording_thread.join(timeout=1.0)
                
            self.showSegmentResults(poprawne_slowa, powtórzone_słowa, is_replay=True)
            
        except Exception as e:
            self.is_timer_active = False
            self.countdown_timer.stop()
            QMessageBox.warning(self, "Błąd", f"Nie można powtórzyć segmentu: {e}")

    def showSegmentResults(self, poprawne_slowa, powtórzone_słowa, is_replay=False):
        """Wyświetla wyniki segmentu z lepszą nawigacją i porównaniem odpowiedzi."""
        self.clearLayout()
        
        # Results display
        self.results_text = QTextEdit()  # Make it instance variable
        self.results_text.setReadOnly(True)
        current_words = self.audio_helper.get_current_segment_words()
        wynik = f"{len(poprawne_slowa)}/{len(current_words)}"
        
        # Show attempt info and progress
        segment_info = f"Segment {self.current_segment + 1} z {self.total_segments}"
        attempt_info = " (Powtórka)" if is_replay else ""
        
        self.results_text.append(f"{segment_info}{attempt_info}\n")
        self.results_text.append(f"Wynik: {wynik}\n")
        
        # Ukryj słowa do powtórzenia początkowo
        self.results_text.append("\nTwoje odpowiedzi:\n")
        for word in powtórzone_słowa:
            if word in current_words:
                self.results_text.append(f"✓ {word} (prawidłowe)\n")
            else:
                self.results_text.append(f"✗ {word} (nieprawidłowe)\n")
        
        # Ustaw style dla tekstu
        self.results_text.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                line-height: 1;
                padding: 10px;
            }
        """)
        
        self.layout.addWidget(self.results_text)
        
        # Add button to show reference words
        show_words_btn = QPushButton("Pokaż słowa do powtórzenia")
        show_words_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        def show_reference_words():
            # Dodaj słowa referencyjne do wyników
            self.results_text.append("\nSłowa do powtórzenia:\n")
            for word in current_words:
                if word in poprawne_slowa:
                    self.results_text.append(f"✓ {word} (poprawnie powiedziane)\n")
                else:
                    self.results_text.append(f"✗ {word} (nie powiedziane)\n")
            show_words_btn.setEnabled(False)  # Disable button after showing words
        
        show_words_btn.clicked.connect(show_reference_words)
        self.layout.addWidget(show_words_btn)
        
        # Navigation buttons
        btn_layout = QHBoxLayout()
        
        replay_btn = QPushButton("Powtórz ten segment")
        replay_btn.clicked.connect(self.replayCurrentSegment)
        btn_layout.addWidget(replay_btn)
        
        if self.current_segment + 1 < self.total_segments:
            next_btn = QPushButton("Następne 5 słów")
            next_btn.clicked.connect(self.nextSegment)
            btn_layout.addWidget(next_btn)
        
        finish_btn = QPushButton("Zakończ ćwiczenie")
        finish_btn.clicked.connect(self.showAudioFiles)
        btn_layout.addWidget(finish_btn)
        
        self.layout.addLayout(btn_layout)
        
        # Save results
        nazwa_pliku = os.path.basename(self.plik_audio)
        attempt_suffix = "_retry" if is_replay else ""
        zapisz_wynik(self.login, 
                    f"{nazwa_pliku}_segment_{self.current_segment + 1}{attempt_suffix}", 
                    poprawne_slowa, powtórzone_słowa, 
                    current_words, self.folder_zapisu)

    def nextSegment(self):
        self.current_segment += 1
        self.startSegmentTest()
        
    def clearLayout(self):
        self.is_timer_active = False  # Stop timer when clearing layout
        self.countdown_timer.stop()
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
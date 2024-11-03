import os
import sys
import time
import datetime
import threading
import soundfile as sf
import unicodedata
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QLineEdit, QListWidget, 
                            QMessageBox, QFileDialog, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from library import zapisz_wynik, rozpoznaj_slowa_z_pliku, powtorz_słowa, odtwarzaj_audio
import pygame  
from library import AUDIOLIB

class Config:
    DEFAULT_SEGMENT_DURATION = 5
    WORDS_PER_CHAPTER = 5
    RESULTS_FOLDER = "wyniki/"
    AUDIO_FOLDER = "audio/demony/"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.audio_helper = AUDIOLIB(self.config)
        self.initUI()
        self.initVariables()
        self.current_segment = 0
        self.total_segments = 0
        
    def initVariables(self):
        self.login = ""
        self.folder_zapisu = self.config.RESULTS_FOLDER
        self.katalog_audio = self.config.AUDIO_FOLDER
        self.plik_audio = None
        
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
        if self.current_segment >= self.total_segments:
            QMessageBox.information(self, "Koniec", "Ukończono wszystkie segmenty!")
            self.showAudioFiles()
            return
            
        self.clearLayout()
        info_label = QLabel(f"Przygotuj się do odsłuchania segmentu {self.current_segment + 1} z {self.total_segments}...")
        self.layout.addWidget(info_label)
        
        QTimer.singleShot(1000, self.playCurrentSegment)

    def playCurrentSegment(self):
        try:
            self.clearLayout()
            
            # Show progress
            progress_label = QLabel(f"Segment {self.current_segment + 1} z {self.total_segments}")
            self.layout.addWidget(progress_label)
            
            listening_label = QLabel("Słuchaj uważnie...")
            self.layout.addWidget(listening_label)
            
            QApplication.processEvents()
            
            # Play current segment
            current_words = self.audio_helper.play_segment(self.current_segment, self.plik_audio)
            if not current_words:
                raise Exception("Nie udało się odtworzyć segmentu")
            
            # Show 'speak now' message
            self.clearLayout()
            speak_label = QLabel("TERAZ MOŻESZ MÓWIĆ!")
            speak_label.setStyleSheet("QLabel { color: red; font-size: 24px; font-weight: bold; }")
            speak_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(speak_label)
            
            QApplication.processEvents()
            time.sleep(1)
            
            poprawne_slowa, powtórzone_słowa = powtorz_słowa(current_words)
            self.showSegmentResults(poprawne_slowa, powtórzone_słowa)
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas testu: {e}")

    def showSegmentResults(self, poprawne_slowa, powtórzone_słowa, is_replay=False):
        """Wyświetla wyniki segmentu, uwzględniając powtórki."""
        self.clearLayout()
        
        results_text = QTextEdit()
        results_text.setReadOnly(True)
        current_words = self.audio_helper.get_current_segment_words()
        wynik = f"{len(poprawne_slowa)}/{len(current_words)}"
        
        # Add attempt info if it's a replay
        attempt_info = " (Powtórka)" if is_replay else ""
        results_text.append(f"Wynik segmentu {self.current_segment + 1}{attempt_info}: {wynik}\n")
        results_text.append(f"Słowa do powtórzenia: {', '.join(current_words)}\n")
        results_text.append(f"Twoje słowa: {', '.join(powtórzone_słowa)}\n")
        results_text.append(f"Poprawne słowa: {', '.join(poprawne_slowa)}\n")
        
        # Add confirmation message for next segment
        if self.current_segment + 1 < self.total_segments:
            next_segment_label = QLabel("Czy chcesz przejść do następnych 5 słów?")
            next_segment_label.setStyleSheet("QLabel { color: blue; font-size: 16px; }")
            next_segment_label.setAlignment(Qt.AlignCenter)
        
        # Add buttons layout
        button_layout = QHBoxLayout()
        replay_btn = QPushButton("Powtórz obecne słowa")
        
        if self.current_segment + 1 < self.total_segments:
            continue_btn = QPushButton("Tak, następne słowa")
        else:
            continue_btn = QPushButton("Zakończ")
            
        finish_btn = QPushButton("Wróć do wyboru pliku")
        
        replay_btn.clicked.connect(self.replayCurrentSegment)
        continue_btn.clicked.connect(self.nextSegment)
        finish_btn.clicked.connect(self.showAudioFiles)
        
        button_layout.addWidget(replay_btn)
        button_layout.addWidget(continue_btn)
        button_layout.addWidget(finish_btn)
        
        self.layout.addWidget(results_text)
        if self.current_segment + 1 < self.total_segments:
            self.layout.addWidget(next_segment_label)
        self.layout.addLayout(button_layout)
        
        # Save results
        nazwa_pliku = os.path.basename(self.plik_audio)
        attempt_suffix = "_retry" if is_replay else ""
        zapisz_wynik(self.login, 
                    f"{nazwa_pliku}_segment_{self.current_segment + 1}{attempt_suffix}", 
                    poprawne_slowa, powtórzone_słowa, 
                    current_words, self.folder_zapisu)

    def replayCurrentSegment(self):
        """Powtarza odtwarzanie aktualnego segmentu dla nowej próby."""
        try:
            self.clearLayout()
            
            # Show replay message
            replay_label = QLabel("Powtórka segmentu - spróbuj jeszcze raz!")
            replay_label.setStyleSheet("QLabel { color: blue; font-size: 18px; }")
            replay_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(replay_label)
            
            QApplication.processEvents()
            time.sleep(1)
            
            # Play audio again
            if not self.audio_helper.replay_current_segment():
                raise Exception("Nie można powtórzyć segmentu")
                
            # Show speak message
            self.clearLayout()
            speak_label = QLabel("TERAZ MOŻESZ MÓWIĆ!")
            speak_label.setStyleSheet("QLabel { color: red; font-size: 24px; font-weight: bold; }")
            speak_label.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(speak_label)
            QApplication.processEvents()
            
            time.sleep(1)
            
            # Get new attempt
            current_words = self.audio_helper.get_current_segment_words()
            poprawne_slowa, powtórzone_słowa = powtorz_słowa(current_words)
            
            # Show updated results with attempt number
            self.showSegmentResults(poprawne_slowa, powtórzone_słowa, is_replay=True)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie można powtórzyć segmentu: {e}")

    def nextSegment(self):
        self.current_segment += 1
        self.startSegmentTest()
        
    def clearLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
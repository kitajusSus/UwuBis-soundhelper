import os
import sys
import time
import datetime
import threading
import soundfile as sf
import unicodedata
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QListWidget, 
                            QMessageBox, QFileDialog, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from library import zapisz_wynik, rozpoznaj_slowa_z_pliku, powtorz_słowa, odtwarzaj_audio
import pygame  
from library import AudioHelper

class Config:
    DEFAULT_SEGMENT_DURATION = 5
    WORDS_PER_CHAPTER = 5
    RESULTS_FOLDER = "wyniki/"
    AUDIO_FOLDER = "audio/demony/"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.audio_helper = AudioHelper(self.config)
        self.initUI()
        self.initVariables()
        
    def initVariables(self):
        self.login = ""
        self.folder_zapisu = self.config.RESULTS_FOLDER
        self.katalog_audio = self.config.AUDIO_FOLDER
        self.plik_audio = None
        
    def initUI(self):
        self.setWindowTitle('UwuBiś Audio Helper')
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
            self.startTest()
        else:
            QMessageBox.critical(self, "Błąd", "Nie udało się załadować pliku audio")

    def startTest(self):
        if not self.audio_helper.has_next_chapter():
            QMessageBox.information(self, "Koniec", "Ukończono wszystkie rozdziały!")
            self.showAudioFiles()
            return
            
        self.clearLayout()
        info_label = QLabel("Przygotuj się do odsłuchania...")
        self.layout.addWidget(info_label)
        
        QTimer.singleShot(2000, lambda: self.playAudioAndTest(self.audio_helper.current_chapter))

    def playAudioAndTest(self, chapter_idx):
        try:
            self.clearLayout()
            current_words = self.audio_helper.play_chapter(chapter_idx, self.plik_audio)
            if not current_words:
                raise Exception("Nie udało się odtworzyć audio")
                
            # Show current progress
            progress_label = QLabel(f"Rozdział {chapter_idx + 1} z {len(self.audio_helper.rozdziały)}")
            self.layout.addWidget(progress_label)
            
            listening_label = QLabel("Słuchaj uważnie...")
            self.layout.addWidget(listening_label)
            
            # Get user's response
            repeat_label = QLabel("Powtórz usłyszane słowa...")
            self.layout.addWidget(repeat_label)
            
            poprawne_slowa, powtórzone_słowa = powtorz_słowa(current_words)
            self.showResults(chapter_idx, poprawne_slowa, powtórzone_słowa)
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas testu: {e}")

    def showResults(self, chapter_idx, poprawne_slowa, powtórzone_słowa):
        self.clearLayout()
        
        # Show results
        results_text = QTextEdit()
        results_text.setReadOnly(True)
        current_words = self.audio_helper.get_current_words()
        wynik = f"{len(poprawne_slowa)}/{len(current_words)}"
        results_text.append(f"Wynik: {wynik}\n")
        results_text.append(f"Słowa do powtórzenia: {', '.join(current_words)}\n")
        results_text.append(f"Twoje słowa: {', '.join(powtórzone_słowa)}\n")
        results_text.append(f"Poprawne słowa: {', '.join(poprawne_slowa)}\n")
        
        # Ask if ready to continue
        ready_label = QLabel("Czy jesteś gotowy na następne słowa?")
        continue_btn = QPushButton("Tak, kontynuuj")
        finish_btn = QPushButton("Zakończ")
        
        continue_btn.clicked.connect(self.continueToNextChapter)
        finish_btn.clicked.connect(self.showAudioFiles)
        
        self.layout.addWidget(results_text)
        self.layout.addWidget(ready_label)
        self.layout.addWidget(continue_btn)
        self.layout.addWidget(finish_btn)
        
        # Save results
        nazwa_pliku = os.path.basename(self.plik_audio)
        zapisz_wynik(self.login, nazwa_pliku, 
                    poprawne_slowa, powtórzone_słowa, 
                    current_words, self.folder_zapisu)

    def continueToNextChapter(self):
        self.current_chapter += 1
        self.startTest()
        
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


import os
import time
import random
from library import zapisz_wynik, rozpoznaj_slowa_z_pliku, powtorz_słowa, odtwarzaj_audio
from PyQt5 import QtWidgets, QtCore, QtGui
import openpyxl
import datetime
import threading
import sys


class uwubis(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aplikacja UwuBiś")
        self.setGeometry(100, 100, 800, 600)
        self.login = ""
        self.wynik = ""
        self.czas_start = datetime.datetime.now()
        self.folder_zapisu = "wyniki/"  # Folder do zapisu wyników
        self.katalog_audio = "audio/demony/"  # Katalog z plikami audio (ustawiany przez użytkownika)
        self.ile_slow_do_rozpoznania = 5
        self.plik_audio = ""
        self.słowa_w_pliku = []
        self.rozdziały = []
        self.wyniki_użytkownika = {}
        self.ekrany = []
        self.aktualny_ekran = None
        self.current_chapter = 0

        self.login_screen()

    def login_screen(self):
        """
        Display the login screen.
        """
        self.clear_screen()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtWidgets.QLabel("Login:"))
        self.login_input = QtWidgets.QLineEdit()
        layout.addWidget(self.login_input)
        login_button = QtWidgets.QPushButton("Zaloguj się")
        login_button.clicked.connect(self.sprawdź_login)
        layout.addWidget(login_button)
        back_button = QtWidgets.QPushButton("Cofnij")
        back_button.clicked.connect(self.cofnij)
        layout.addWidget(back_button)

    def sprawdź_login(self):
        """
        Check the login credentials.
        """
        self.login = self.login_input.text()
        if self.login == "test":  # Przykładowy login
            self.wybierz_folder_audio_screen()
        else:
            QtWidgets.QMessageBox.critical(self, "Błąd", "Niepoprawny login")

    def wybierz_folder_audio_screen(self):
        """
        Display the screen to choose the audio folder.
        """
        self.clear_screen()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        choose_folder_button = QtWidgets.QPushButton("Wybierz folder z plikami audio")
        choose_folder_button.clicked.connect(self.wybierz_folder_audio)
        layout.addWidget(choose_folder_button)
        back_button = QtWidgets.QPushButton("Cofnij")
        back_button.clicked.connect(self.cofnij)
        layout.addWidget(back_button)

    def wybierz_folder_audio(self):
        """
        Open a dialog to choose the audio folder.
        """
        try:
            self.katalog_audio = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder")
            if self.katalog_audio:
                self.pliki_audio_screen()
            else:
                QtWidgets.QMessageBox.critical(self, "Błąd", "Nie wybrano folderu")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {e}")

    def pliki_audio_screen(self):
        """
        Display the screen to choose an audio file.
        """
        self.clear_screen()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        try:
            self.pliki_audio = [f for f in os.listdir(self.katalog_audio) if f.endswith('.wav')]
            if not self.pliki_audio:
                QtWidgets.QMessageBox.critical(self, "Błąd", "Brak plików audio w wybranym folderze")
                self.cofnij()
                return
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {e}")
            self.cofnij()
            return

        self.listbox = QtWidgets.QListWidget()
        for plik in self.pliki_audio:
            self.listbox.addItem(plik)
        layout.addWidget(self.listbox)
        choose_file_button = QtWidgets.QPushButton("Wybierz plik audio")
        choose_file_button.clicked.connect(self.wybierz_plik_audio)
        layout.addWidget(choose_file_button)
        back_button = QtWidgets.QPushButton("Cofnij")
        back_button.clicked.connect(self.cofnij)
        layout.addWidget(back_button)

    def wybierz_plik_audio(self):
        """
        Choose an audio file and process it.
        """
        try:
            self.plik_audio = os.path.join(self.katalog_audio, self.listbox.currentItem().text())
            self.słowa_w_pliku = rozpoznaj_slowa_z_pliku(self.plik_audio, len(rozpoznaj_slowa_z_pliku(self.plik_audio, 1000)))
            self.rozdziały = [self.słowa_w_pliku[i:i + self.ile_slow_do_rozpoznania] for i in range(0, len(self.słowa_w_pliku), self.ile_slow_do_rozpoznania)]
            self.rozdziały_screen()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {e}")
            self.cofnij()

    def rozdziały_screen(self):
        """
        Display the screen to choose a chapter.
        """
        self.clear_screen()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.listbox = QtWidgets.QListWidget()
        for i, rozdział in enumerate(self.rozdziały):
            self.listbox.addItem(f"Rozdział {i+1}: {' '.join(rozdział)}")
        layout.addWidget(self.listbox)
        choose_chapter_button = QtWidgets.QPushButton("Wybierz rozdział")
        choose_chapter_button.clicked.connect(self.wybierz_rozdział)
        layout.addWidget(choose_chapter_button)
        back_button = QtWidgets.QPushButton("Cofnij")
        back_button.clicked.connect(self.cofnij)
        layout.addWidget(back_button)
        self.wynik_label = QtWidgets.QLabel("Wynik:")
        layout.addWidget(self.wynik_label)

    def wybierz_rozdział(self):
        """
        Choose a chapter and start the test.
        """
        wybrany_rozdział = self.listbox.currentItem().text()
        numer_rozdziału = int(wybrany_rozdział.split(":")[0].split()[-1]) - 1
        słowa_w_rozdziale = self.rozdziały[numer_rozdziału]
        if numer_rozdziału in self.wyniki_użytkownika:
            self.wynik_label.setText(f"Wynik:  {self.wyniki_użytkownika[numer_rozdziału]}")
        else:
            self.wynik_label.setText("Brak wyniku")
        threading.Thread(target=self.przebieg_testu, args=(numer_rozdziału,)).start()

    def przebieg_testu(self, numer_rozdziału):
        """
        Conduct the test for the chosen chapter.
        """
        self.current_chapter = numer_rozdziału  # Ustawienie current_chapter
        self.clear_screen()
        odtwarzaj_audio(self.plik_audio)  # Odtwarzaj cały plik audio (do poprawy: odtwarzaj tylko wybrany rozdział)
        time.sleep(1)  # Czas na zastanowienie

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QtWidgets.QLabel("Powtórz słowa które usłyszałeś"))

        poprawne_slowa, powtórzone_słowa = powtorz_słowa(self.rozdziały[numer_rozdziału])
        wynik = f"{len(poprawne_slowa)}/{len(self.rozdziały[numer_rozdziału])}"
        self.wyniki_użytkownika[numer_rozdziału] = wynik
        self.zapytaj_o_dalsze(numer_rozdziału, wynik, poprawne_slowa, powtórzone_słowa, self.rozdziały[numer_rozdziału])

    def informacja_screen(self, numer_rozdziału):
        """
        Display the information screen before starting the audio playback.
        """
        self.clear_screen()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtWidgets.QLabel("Za sekundę rozpocznie się odtwarzanie audio...", wordWrap=True, alignment=QtCore.Qt.AlignCenter))
        QtCore.QTimer.singleShot(1000, lambda: self.odtwórz_audio_ikontynuuj(numer_rozdziału))  # Po sekundzie uruchom odtwarzanie audio

    def odtwórz_audio_ikontynuuj(self, numer_rozdziału):
        """
        Play the audio and continue the test.
        """
        self.clear_screen()
        odtwarzaj_audio(self.plik_audio)  # Odtwarzaj cały plik audio (do poprawy: odtwarzaj tylko wybrany rozdział)
        time.sleep(1)  # Czas na zastanowienie
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QtWidgets.QLabel("Powtórz usłyszane słowa...", wordWrap=True, alignment=QtCore.Qt.AlignCenter))
        poprawne_slowa, powtórzone_słowa = powtorz_słowa(self.rozdziały[numer_rozdziału])
        wynik = f"{len(poprawne_slowa)}/{len(self.rozdziały[numer_rozdziału])}"
        self.wyniki_użytkownika[numer_rozdziału] = wynik
        self.zapytaj_o_dalsze(numer_rozdziału, wynik, poprawne_slowa, powtórzone_słowa, self.rozdziały[numer_rozdziału])

    def zapytaj_o_dalsze(self, numer_rozdziału, wynik, poprawne_słowa, powtórzone_słowa, słowa_w_rozdziale):
        """
        Ask the user what to do next after the test.
        """
        self.clear_screen()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QtWidgets.QLabel(f"Wynik: {wynik}"))

        zapisz_wynik(self.login, self.plik_audio, słowa_w_rozdziale, powtórzone_słowa, wynik, self.folder_zapisu)

        self.wyświetl_statystyki(słowa_w_rozdziale, poprawne_słowa, powtórzone_słowa)
        choose_chapter_button = QtWidgets.QPushButton("Wybierz kolejny rozdział")
        choose_chapter_button.clicked.connect(self.rozdziały_screen)
        layout.addWidget(choose_chapter_button)
        back_button = QtWidgets.QPushButton("Cofnij")
        back_button.clicked.connect(self.cofnij)
        layout.addWidget(back_button)

    def cofnij(self):
        """
        Go back to the previous screen.
        """
        if self.ekrany:
            self.clear_screen()
            self.aktualny_ekran = self.ekrany.pop()
            self.setLayout(self.aktualny_ekran)

    def powtórz_audio(self, numer_rozdziału):
        """
        Repeat the audio for the given chapter.
        """
        self.close()
        threading.Thread(target=self.przebieg_testu, args=(numer_rozdziału,)).start()

    def wyświetl_statystyki_i_zakończ(self, słowa_w_rozdziale, poprawne_słowa, powtórzone_słowa):
        """
        Display the statistics and end the application.
        """
        self.close()
        self.statystyki_window = QtWidgets.QWidget()
        self.statystyki_window.setWindowTitle("Aplikacja UwuBiś - Statystyki")
        layout = QtWidgets.QVBoxLayout()
        self.statystyki_window.setLayout(layout)
        self.statystyki_text = QtWidgets.QTextEdit()
        self.statystyki_text.setReadOnly(True)
        layout.addWidget(self.statystyki_text)
        self.statystyki_text.append(f"Poprawnie powtórzone słowa: {len(poprawne_słowa)}/{len(słowa_w_rozdziale)}\n")
        for i, (słowo, powtórzone) in enumerate(zip(słowa_w_rozdziale, powtórzone_słowa), start=1):
            self.statystyki_text.append(f"{i}. {słowo} -> {powtórzone}\n")
        close_button = QtWidgets.QPushButton("Zakończ")
        close_button.clicked.connect(self.statystyki_window.close)
        layout.addWidget(close_button)
        back_button = QtWidgets.QPushButton("Cofnij")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)
        self.statystyki_window.show()

    def wyświetl_statystyki(self, słowa_w_rozdziale, poprawne_słowa, powtórzone_słowa):
        """
        Display the statistics.
        """
        self.statystyki_text = QtWidgets.QTextEdit()
        self.statystyki_text.setReadOnly(True)
        self.layout().addWidget(self.statystyki_text)
        self.statystyki_text.append(f"Poprawnie powtórzone słowa: {len(poprawne_słowa)}/{len(słowa_w_rozdziale)}\n")
        for i, (słowo, powtórzone) in enumerate(zip(słowa_w_rozdziale, powtórzone_słowa), start=1):
            self.statystyki_text.append(f"{i}. {słowo} -> {powtórzone}\n")

        # przyciski
        repeat_audio_button = QtWidgets.QPushButton("Odtwórz to samo audio")
        repeat_audio_button.clicked.connect(lambda: self.powtórz_audio(self.current_chapter))
        self.layout().addWidget(repeat_audio_button)
        next_audio_button = QtWidgets.QPushButton("Dalej")
        next_audio_button.clicked.connect(self.odtwórz_kolejny_audio)
        self.layout().addWidget(next_audio_button)
        close_button = QtWidgets.QPushButton("Zakończ")
        close_button.clicked.connect(self.close)
        self.layout().addWidget(close_button)
        back_button = QtWidgets.QPushButton("Cofnij")
        back_button.clicked.connect(self.wybierz_folder_audio_screen)
        self.layout().addWidget(back_button)

    def odtwórz_kolejny_audio(self):
        """
        Play the next audio chapter.
        """
        self.current_chapter += 1
        if self.current_chapter < len(self.rozdziały):
            self.close()
            threading.Thread(target=self.przebieg_testu, args=(self.current_chapter,)).start()
        else:
            QtWidgets.QMessageBox.information(self, "Koniec", "To był ostatni rozdział.")

    def go_back(self):
        """
        Go back to the previous screen.
        """
        if self.ekrany:
            self.clear_screen()
            self.aktualny_ekran = self.ekrany.pop()
            self.setLayout(self.aktualny_ekran)

    def clear_screen(self):
        """
        Clear the current screen.
        """
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.chdir(sys._MEIPASS)
    app = QtWidgets.QApplication(sys.argv)
    window = uwubis()
    window.show()
    sys.exit(app.exec_())

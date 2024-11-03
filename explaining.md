# UwuBiś Audio Helper - Analiza Kodu Linijka po Linijce 🔍

## 1. Importowane Biblioteki


## main_new.py - Główny Program


# UwuBiś Audio Helper - Szczegółowe Wyjaśnienie 🎯

## 1. Wprowadzenie 🌟
Program UwuBiś to narzędzie do nauki poprzez słuchanie i powtarzanie słów. Działa jak przyjazny nauczyciel, który:
- Odtwarza ci nagrania
- Słucha, jak powtarzasz słowa
- Sprawdza, czy dobrze je powtórzyłeś
- Zapisuje twoje postępy

## 2. Struktura Programu ���️

### main_new.py - Główny Program
Zawiera interfejs użytkownika i główną logikę programu:

#### Klasa MainWindow:
1. __init__ i initVariables:
   - Tworzy okno programu
   - Ustawia początkowe wartości (login, folder z plikami, itp.)
   ```python
   class MainWindow:
    def initVariables(self):
        self.login = ""  # przechowuje nazwę użytkownika
        self.current_chapter = 0  # aktualny fragment audio (0 = pierwszy)
        self.folder_zapisu = "wyniki/"  # gdzie zapisują się rezultaty testów
        self.katalog_audio = "audio/demony/"  # lokalizacja plików dźwiękowych
        self.ile_slow_do_rozpoznania = 5  # ile słów w jednym teście
        self.słowa_w_pliku = []  # wszystkie słowa z pliku audio
        self.rozdziały = []  # słowa podzielone na grupy po 5
        self.wyniki_użytkownika = {}  # słownik wyników dla każdego rozdziału
   ```


2. Funkcje interfejsu:
   - showLoginScreen(): Pokazuje ekran logowania
   ```python
   def showLoginScreen(self):
    self.clearLayout()  # usuwa poprzednie elementy
    login_label = QLabel("Login:")  # etykieta "Login"
    self.login_input = QLineEdit()  # pole do wpisania loginu
    login_button = QPushButton("Zaloguj się")  # przycisk logowania
   ```
   - showFolderSelection(): Pozwala wybrać folder z plikami
   - showAudioFiles(): Wyświetla listę plików audio
   - showResults(): Pokazuje wyniki testu

   ```python
   def initUI(self):
    self.setWindowTitle('UwuBiś Audio Helper')  # nazwa okna
    self.setGeometry(100, 100, 800, 600)  # pozycja i rozmiar okna (x, y, szerokość, wysokość)
    self.central_widget = QWidget()  # główny widget
    self.setCentralWidget(self.central_widget)  # ustawienie widgetu centralnego
    self.layout = QVBoxLayout(self.central_widget)  # układ pionowy
   ```

3. Funkcje obsługi dźwięku:
   - handleAudioFileSelection(): Przygotowuje plik do odtworzenia
   ```python
   def handleAudioFileSelection(self):
    # Sprawdza czy wybrano plik
    if not self.file_list.currentItem():
        return
        
    # Tworzy pełną ścieżkę do pliku
    selected_file = self.file_list.currentItem().text()
    self.plik_audio = os.path.join(self.katalog_audio, selected_file)
    
    # Przetwarza plik audio
    self.słowa_w_pliku = rozpoznaj_slowa_z_pliku(self.plik_audio, 1000)
    
    # Normalizuje tekst (polskie znaki)
    normalized_words = [unicodedata.normalize('NFKC', word) for word in self.słowa_w_pliku]
    
    # Dzieli na grupy po 5 słów
    self.rozdziały = [normalized_words[i:i + self.ile_slow_do_rozpoznania] 
                    for i in range(0, len(normalized_words), self.ile_slow_do_rozpoznania)]
   ```
   - playAudioAndTest(): Odtwarza dźwięk i przeprowadza test
   - startTest(): Rozpoczyna nowy test
   ```python
   def startTest(self):
    # Sprawdza czy są jeszcze rozdziały do przetestowania
    if self.current_chapter >= len(self.rozdziały):
        return
        
    # Pokazuje komunikat przygotowawczy
    info_label = QLabel("Przygotuj się do odsłuchania...")
    
    # Uruchamia test po 2 sekundach
    QTimer.singleShot(2000, lambda: self.playAudioAndTest(self.current_chapter))
   ```
   Odtwarzanie i testowanie:
   ```python
   def playAudioAndTest(self, chapter_idx):
    # Oblicza czas początku i końca fragmentu
    start_time = chapter_idx * self.ile_slow_do_rozpoznania * 1000
    end_time = (chapter_idx + 1) * self.ile_slow_do_rozpoznania * 1000
    
    # Odtwarza audio w osobnym wątku
    threading.Thread(target=odtwarzaj_audio, 
                  args=(self.plik_audio, start_time, end_time)).start()
    
    # Czeka na odpowiedź użytkownika
    poprawne_slowa, powtórzone_słowa = powtorz_słowa(self.rozdziały[chapter_idx])
    
    # Oblicza wynik
    wynik = f"{len(poprawne_slowa)}/{len(self.rozdziały[chapter_idx])}"
   ```

### library.py - Biblioteka Pomocnicza
Zawiera funkcje do:
1. zapisz_wynik():
   - Zapisuje wyniki do pliku Excel
   - Śledzi postępy użytkownika
   ```python
   def zapisz_wynik(login, nazwa_audio, poprawne_słowa, powtórzone_słowa, słowa, folder_zapisu):
    # Tworzy nazwę pliku Excel
    nazwa_pliku = os.path.join(folder_zapisu, f"{login}.xlsx")
    
    # Tworzy folder jeśli nie istnieje
    if not os.path.exists(folder_zapisu):
        os.makedirs(folder_zapisu)
    
    # Tworzy nowy plik Excel jeśli nie istnieje
    if not os.path.exists(nazwa_pliku):
        df = pd.DataFrame(columns=[
            "Numer podejścia",
            "Nazwa Pliku i rozdział",
            "Słowa w pliku",
            "Słowa poprawne",
            "Słowa niepoprawne",
            "Wynik",
            "Maksymalny Wynik"
        ])
        df.to_excel(nazwa_pliku, index=False)
    ```

2. rozpoznaj_slowa_z_pliku():
   - Zamienia dźwięk na tekst
   - Wyodrębnia słowa z nagrania

3. powtorz_słowa():
   - Nagrywa głos użytkownika
   - Sprawdza poprawność wypowiedzianych słów

4. odtwarzaj_audio():
   - Odtwarza fragmenty plików dźwiękowych
   - Kontroluje długość odtwarzania

## 3. Jak Program Działa? 🎮

### Krok 1: Logowanie
- Uruchamiasz program
- Wpisujesz login (na razie działa z loginem "test")
- Program sprawdza, czy możesz się zalogować

### Krok 2: Wybór Materiału
- Wybierasz folder z plikami audio
- Widzisz listę dostępnych nagrań
- Wybierasz plik do nauki

### Krok 3: Nauka
- Program dzieli nagranie na części po 5 słów
- Odtwarza ci pierwszą część
- Czeka na twoje powtórzenie
- Sprawdza, czy dobrze powtórzyłeś

### Krok 4: Wyniki
- Pokazuje, które słowa były poprawne
- Zapisuje twój wynik
- Pyta, czy chcesz kontynuować

## 4. Techniczne Szczegóły 🔧

### Przechowywanie Danych
- Login użytkownika
- Aktualny rozdział
- Folder z wynikami ("wyniki/")
- Folder z nagraniami ("audio/demony/")
- Lista słów do nauczenia
- Wyniki użytkownika

### Format Zapisu Wyników
Excel zawiera:
- Numer podejścia
- Nazwę pliku
- Słowa w pliku
- Słowa poprawne
- Słowa niepoprawne
- Wynik
- Maksymalny możliwy wynik

## 5. Wskazówki Użytkowania 💡
1. Używaj dobrego mikrofonu
2. Mów wyraźnie i niezbyt szybko
3. Czekaj na sygnał przed mówieniem
4. Możesz przerwać w dowolnym momencie
5. Wyniki są zapisywane automatycznie

## 6. Rozwiązywanie Problemów 🔍
- Jeśli program nie rozpoznaje słów: sprawdź mikrofon
- Jeśli nie słyszysz dźwięku: sprawdź głośniki
- Jeśli wyniki się nie zapisują: sprawdź uprawnienia do folderu "wyniki"

## 7. Plany Rozwoju 🚀
- Dodanie więcej opcji logowania
- Rozszerzenie bazy nagrań
- Dodanie statystyk postępów
- Wprowadzenie poziomów trudności
- Dodanie trybu nauki z powtórkami

## 8. Ważne Mechanizmy
1. Wielowątkowość:
- Odtwarzanie audio w osobnym wątku
- Interfejs pozostaje responsywny podczas odtwarzania
2. Normalizacja Tekstu
- Obsługa polskich znaków
- Ujednolicenie formatowania tekstu
3. Zarządzanie Pamięcią
- Czyszczenie layoutu przed zmianą widoku
- Zwalnianie zasobów audio po użyciu
## 9. Przepływ Danych w Programie
- Input użytkownika (login) → walidacja → dostęp do programu
- Wybór pliku → przetwarzanie audio → lista słów
- Podział na rozdziały → odtwarzanie → nagrywanie odpowiedzi
- Analiza odpowiedzi → obliczenie wyniku → zapis do Excel
- Aktualizacja interfejsu → pokazanie wyników → następny rozdział
## 10. Optymalizacja i Wydajność
- Opóźnione ładowanie plików audio
- Przechowywanie tylko potrzebnych danych w pamięci
- Asynchroniczne odtwarzanie dźwięku
- Efektywne zarządzanie zasobami systemu
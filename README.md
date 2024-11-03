# Projekt UwuBiś

## 1. O projekcie

### Opis
> "słysząc jakiś ciąg słów (np. 5 słów z audiobooka), człowiek z implantem chce sprawdzić, czy wszystko poprawnie zrozumiał. Musi więc zapisać sobie słowa które usłyszał, a następnie porównać z faktycznymi słowami (np. sprawdzając w wersji papierowej książki) i zobaczyć ile słów zrozumiał poprawnie." lic. Przemysław Bańkowski. 

### Wymagania
- Python 3.11
- Biblioteki:
  - `speech_recognition` 3.11.0
  - `sounddevice` 72.1.0
  - `soundfile` 0.12.0
  - `numpy` 2.1.1
  - `pandas` 2.1.1
  - `openpyxl` 3.1.2

Instalacja bibliotek
```sh
pip install speechrecognition sounddevice soundfile numpy pandas openpyxl
```
## Tworzenie wirtualnego środowiska (opcjonalne)

### Uruchamianie
Umieść plik audio (np. audio1.wav) w katalogu audio\

Uruchom skrypt:
```python
python main.py
```


## Ogólne wytłumaczenie poszczególnych funkcji. 

1. Losowanie pliku audio: Skrypt losuje plik audio z katalogu.
2. Odtwarzanie pliku audio: Skrypt odtwarza wybrany plik audio, aby użytkownik mógł go usłyszeć.
3. Nagrywanie odpowiedzi użytkownika: Po odtworzeniu pliku audio, skrypt prosi użytkownika o powtórzenie usłyszanych słów i nagrywa jego odpowiedź.
4. Rozpoznawanie mowy: Skrypt używa biblioteki speechrecognition, aby rozpoznać słowa wypowiedziane przez użytkownika.
5. Porównywanie słów: Skrypt porównuje słowa wypowiedziane przez użytkownika z oryginalnymi słowami z pliku audio.
6. Zapisywanie wyników: Skrypt zapisuje wyniki do pliku Excel, w którym znajdują się informacje o poprawnie i niepoprawnie powtórzonych słowach.

## Wytłumacznie właściwości kodu, co do czego i po co.

### 1. `threading`
1. `threading` to standardowy moduł Pythona służący do obsługi wielowątkowości. Pozwala na:
- Równoległe wykonywanie zadań
- Zarządzanie wieloma operacjami jednocześnie
- Poprawę wydajności aplikacji, szczególnie przy operacjach I/O

Przykład użycia:
```python
import threading

def moje_zadanie():
    print("Wykonuję zadanie w osobnym wątku")

# Tworzenie nowego wątku
watek = threading.Thread(target=moje_zadanie)
watek.start()  # Uruchomienie wątku
watek.join()   # Oczekiwanie na zakończenie wątku
```
W kontekście aplikacji audio, threading jest szczególnie przydatny do:

- Odtwarzania dźwięku w tle
- Nagrywania audio bez blokowania interfejsu
- Przetwarzania dźwięku równolegle z innymi operacjami

**Obszerniejszy przykład**

```python
import threading
import time
from playsound import playsound  # dla przykładu

class AudioPlayer:
    def __init__(self):
        self.is_playing = False
        
    def play_audio_file(self, file_path):
        # Funkcja odtwarzająca dźwięk w osobnym wątku
        def play():
            self.is_playing = True
            playsound(file_path)
            self.is_playing = False
            
        # Utworzenie i uruchomienie wątku
        audio_thread = threading.Thread(target=play)
        audio_thread.start()

       
        
    def wait_for_completion(self):
        # Czekamy aż dźwięk się skończy
        while self.is_playing:
            time.sleep(0.1)

# Przykład użycia:
player = AudioPlayer()
player.play_audio_file("sample.mp3")  # Rozpoczyna odtwarzanie w tle
print("Możesz wykonywać inne operacje podczas odtwarzania!")
player.wait_for_completion()  # Poczekaj na zakończenie
```
Najbardziej przykuwa uwagę element 
```python
# Utworzenie i uruchomienie wątku
        audio_thread = threading.Thread(target=play)
        audio_thread.start()
```
Już tłumaczę co to robi i po co, dla wygody rozbiję to na części:
1. `threading.Thread(target=play)`:

- Tworzy nowy obiekt wątku
- `target=play` wskazuje funkcję `play` jako kod do wykonania w tym wątku
- `play` to funkcja zdefiniowana wcześniej (bez nawiasów, bo przekazujemy referencję)

2. `audio_thread.start()`:

- Uruchamia utworzony wątek
- Od tego momentu funkcja play wykonuje się równolegle z głównym programem
- Nie blokuje pozostałej części programu


# n. Posłowie 
Moja wizję rozwoju projektu opisałem w [dalszy rozwoj](dalszy_rozwoj.md). 

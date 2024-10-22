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



# n. Posłowie 
Moja wizję rozwoju projektu opisałem w [dalszy rozwoj](dalszy_rozwoj.md). 

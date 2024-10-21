
"""
import pyaudio
import speech_recognition as sr
#from pydub import AudioSegment
#from pydub.playback import play

# Krok 2: Odtwarzanie i Transkrypcja
def odtworz_i_transkrybuj(sciezka_do_pliku):
    sound = AudioSegment.from_file(sciezka_do_pliku)
    play(sound)
    r = sr.Recognizer()
    with sr.AudioFile(sciezka_do_pliku) as source:
        audio = r.record(source)
    try:
        tekst_optymalny = r.recognize_google(audio, language="pl-PL")
        return tekst_optymalny
    except sr.UnknownValueError:
        return "Nie rozpoznano mowy"

# Krok 3: Rejestracja Odpowiedzi
def zarejestruj_odpowiedz():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Mów teraz...")
        audio = r.listen(source)
    try:
        tekst_użytkownika = r.recogn
        """
"""
wygenerowany przez github copilot skrypt służący do szybkiego 
sprawdzenia czy biblioteki potrzebne do uruchomienia skryptu są zainstalowane i  działają poprawnie
- zrezygnowałem z pydub bo  sprawdzałem wiele opcji ale zachowam go jako przypomnienie do dalszego rozwoju projektu bo biblioteka moze być przydatna

"""




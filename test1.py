import soundfile as sf

file_path = 'audio/krzys_audio/audio1.wav'
try:
    audio_data, samplerate = sf.read(file_path)
    print("Plik audio został pomyślnie załadowany.")
except Exception as e:
    print(f"Błąd podczas ładowania pliku audio: {e}")

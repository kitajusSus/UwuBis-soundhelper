from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from library import AUDIOLIB, zapisz_wynik, Config
import logging

app = Flask(__name__)

# Ustawienie ścieżki do folderu z modelem Vosk
app.config['VOSK_MODEL_PATH'] = os.path.join('models', 'vosk-model-small-pl-0.22')

# Konfiguracja aplikacji
config = Config()
audio_helper = AUDIOLIB(config)

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_audio_files')
def get_audio_files():
    audio_files = [f for f in os.listdir(config.AUDIO_FOLDER) if f.endswith('.wav')]
    return jsonify(audio_files)

@app.route('/get_audio/<filename>')
def get_audio(filename):
    return send_from_directory(config.AUDIO_FOLDER, filename)

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        return jsonify({'error': 'Brak pliku audio'}), 400

    audio_file = request.files['audio_data']
    temp_path = 'temp_user_audio.wav'
    audio_file.save(temp_path)

    try:
        # Zakładamy, że current_segment jest przekazywany jako parametr POST
        segment_idx = int(request.form.get('segment_idx', 0))

        # Przetwarzanie audio za pomocą Vosk
        words, similarity = audio_helper.verify_user_audio(segment_idx, temp_path)
        os.remove(temp_path)

        # Zwracanie wyników do klienta
        return jsonify({
            'words': words,
            'similarity': similarity
        })
    except Exception as e:
        logging.error(f"Błąd podczas przetwarzania audio: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
import whisper
import torch


device = "cuda" if torch.cuda.is_available() else "cpu"

model = whisper.load_model("small", device=device)
result = model.transcribe("audio/krzys_audio/audio1.wav")
print(result["text"])

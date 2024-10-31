import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from transformers import BertTokenizer, BertModel

# Zdefiniuj dane
dane = pd.read_csv(f'{login}.csv')

# Przygotuj dane do treningu modelu
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
dane['tekst'] = dane['tekst'].apply(lambda x: tokenizer.encode(x, max_length=512, padding='max_length', truncation=True))

# Zdefiniuj model językowy
class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.bert = BertModel.from_pretrained('bert-base-uncased')
        self.dropout = nn.Dropout(0.1)
        self.fc = nn.Linear(768, 8)

    def forward(self, x):
        x = self.bert(x)['pooler_output']
        x = self.dropout(x)
        x = self.fc(x)
        return x

# Inicjuj model i optymalizator
model = Model()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-5)

# Trenuj model
for epoch in range(5):
    model.train()
    total_loss = 0
    for batch in range(len(dane)):
        input_ids = torch.tensor(dane['tekst'][batch])
        labels = torch.tensor(dane['etykieta'][batch])
        optimizer.zero_grad()
        outputs = model(input_ids)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f'Epoch {epoch+1}, Loss: {total_loss / len(dane)}')

# Wyślij diagnozę i analizę
def wyslij_diagnoze(tekst):
    input_ids = torch.tensor(tokenizer.encode(tekst, max_length=512, padding='max_length', truncation=True))
    outputs = model(input_ids)
    _, predicted = torch.max(outputs, dim=1)
    return predicted.item()

tekst = "To jest przykładowy tekst do analizy."
diagnoza = wyslij_diagnoze(tekst)
print(f'Diagnoza: {diagnoza}')





"""from openai import OpenAI

# Ustaw API key
API_KEY = "YOUR_API_KEY_HERE"

# Ustaw adres URL API
BASE_URL = "https://integrate.api.nvidia.com/v1"

# Utwórz klienta API
client = OpenAI(
  base_url=BASE_URL,
  api_key=API_KEY
)

# Funkcja do generowania tekstu
def generate_text(prompt):
  completion = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-70b-instruct",
    messages=[{"role":"user","content":prompt}],
    temperature=0.5,
    top_p=1,
    max_tokens=1024,
    stream=True
  )
  text = ""
  for chunk in completion:
    if chunk.choices[0].delta.content is not None:
      text += chunk.choices[0].delta.content
  return text

# Przykładowy prompt
prompt = "Write a short story about a character who discovers a hidden world."

# Wygeneruj tekst
text = generate_text(prompt)

# Wyświetl tekst
print(text)"""
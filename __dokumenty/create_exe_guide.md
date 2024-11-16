
JAK STWORZYĆ PLIK .EXE Z PROGRAMU PYTHON - PRZEWODNIK KROK PO KROKU

1. INSTALACJA POTRZEBNYCH NARZĘDZI
   - Otwórz terminal/wiersz poleceń
   - Zainstaluj pyinstaller:
     pip install pyinstaller
   - Upewnij się, że masz zainstalowane wszystkie biblioteki z projektu:
     pip install -r requirements.txt

2. PRZYGOTOWANIE PROJEKTU
   - Upewnij się, że wszystkie pliki projektu są w jednym folderze
   - Sprawdź, czy main.py działa poprawnie
   - Przygotuj folder z plikami audio i innymi zasobami

3. TWORZENIE PLIKU .EXE
   Metoda 1 (Podstawowa):
   - Przejdź do folderu z projektem:
     cd ścieżka/do/twojego/projektu
   - Uruchom pyinstaller:
     pyinstaller --onefile main.py

   Metoda 2 (Zaawansowana z ikoną i zasobami):
   pyinstaller --onefile --windowed --icon=ikona.ico --add-data "audio;audio" --add-data "wyniki;wyniki" main.py

4. SPRAWDZENIE WYNIKÓW
   - Sprawdź folder 'dist' w twoim projekcie
   - Znajdź tam plik main.exe
   - Skopiuj foldery 'audio' i 'wyniki' do folderu z main.exe

5. TESTOWANIE
   - Uruchom main.exe
   - Sprawdź czy:
     * Program się uruchamia
     * Działa logowanie
     * Działa odtwarzanie audio
     * Działa nagrywanie
     * Zapisują się wyniki

6. ROZWIĄZYWANIE PROBLEMÓW
   Jeśli program nie działa:
   - Sprawdź logi w terminalu
   - Dodaj --debug do komendy pyinstaller
   - Upewnij się, że wszystkie pliki są w odpowiednich folderach
   - Sprawdź ścieżki do plików w kodzie

7. DYSTRYBUCJA
   - Stwórz folder "UwuBis"
   - Skopiuj tam:
     * main.exe
     * folder 'audio'
     * folder 'wyniki'
   - Spakuj folder do .zip
   - Program jest gotowy do dystrybucji!

UWAGI:
- Zawsze testuj .exe na czystym systemie
- Pamiętaj o dołączeniu wszystkich zasobów
- Sprawdź uprawnienia do folderów
- Może być potrzebne dodanie antywirusa do wyjątków

PRZYDATNE FLAGI PYINSTALLER:
--onefile : jeden plik exe
--windowed : bez konsoli
--icon : dodaje ikonę
--add-data : dodaje pliki/foldery
--debug : pokazuje więcej informacji o błędach



main_new.spec powinien wygladac mniej wiecej tak, najlepiej by to było wiecej niż mniej 
```bash
# main_new.spec
block_cipher = None

a = Analysis(
    ['main_new.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'openpyxl',
        'openpyxl.cell._writer',
        'openpyxl.cell',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'pygame'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main_new',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```
pyinstaller --clean main_new.spec
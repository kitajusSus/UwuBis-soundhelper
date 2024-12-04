komendy  potrzebne do skompilowania  audio.zig do pliku .dll


```bash
zig build-lib -dynamic audio.zig -target native
```


Parametry:
-`dynamic`: Tworzy współdzieloną bibliotekę (.so na Linuxie, .dll na Windowsie, .dylib na macOS).
-`target native`: Tworzy bibliotekę dla systemu, na którym wykonujemy komendę. Możemy zmienić na inny target, np. `-target x86_64-linux-gnu`.

**Output:**

Po kompilacji w tym samym katalogu powstanie plik:
- audio.so na Linuxie,
- audio.dll na Windowsie,
- audio.dylib na macOS.
Testowanie biblioteki: Użyj ctypes w Pythonie do załadowania i przetestowania funkcji.
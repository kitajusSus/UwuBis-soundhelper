# Krzys i karol work to do: 
By 
## UwuBiś aplikacja do ćwiczenia słuchu. 
1. zrobić by program zapisywał plik w formacie.
- numer podejcia, nazwa pliku, słowa w pliku, słowa powiedziane, słowa nie powiedziane itd, wynik, wynik maksymalny

TAK JEST TERAZ
![zdjecie1](zdjęcia\image.png)


TAK MA BYĆ POTEM
![times](zdjęcia\zdjęcie.png)
2. ZROBIĆ BY PROGRAM ZAPISYWAŁ WYNIKI W FOLDERZE wyniki\


## Błędy / bugi 
1. ***Odtwórz to samo audio.***
jak klikam to 
```bash
 File "d:\python projekty\UwuBis-soundhelper\main.py", line 201, in <lambda>
    tk.Button(self.root, text="Odtwórz to samo audio", command=lambda: self.powtórz_audio(self.current_chapter)).pack(pady=10)
                                                                                          ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Aplikacja' object has no attribute 'current_chapter'
```

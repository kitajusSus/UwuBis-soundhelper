# KKK (Krzyś, Karol, Kamil): 
**Planowanie i analiza wymagań** – przed rozpoczęciem projektu ważne jest zrozumienie oczekiwań użytkownika oraz wymagań technicznych, co umożliwia zaprojektowanie odpowiedniej architektury.

**Modularność i zasada KISS (Keep It Simple, Stupid)** – tworzenie kodu, który jest prosty, czytelny i łatwy w utrzymaniu. Podział na moduły zwiększa elastyczność i ułatwia debugowanie.

**DRY (Don't Repeat Yourself)**– unikanie duplikacji kodu, co redukuje ryzyko błędów i upraszcza proces utrzymania oraz aktualizacji aplikacji.

**Testowanie** – automatyczne testy jednostkowe, integracyjne i akceptacyjne pozwalają na szybkie wykrycie błędów i ich eliminację przed wdrożeniem na produkcję.

**Bezpieczeństwo** – projektowanie i testowanie z myślą o bezpieczeństwie aplikacji, co obejmuje kontrolę dostępu, walidację danych i ochronę przed atakami (np. SQL Injection, XSS).

**Ciągła integracja (CI) i ciągłe wdrażanie (CD)** – procesy automatyzacji, które umożliwiają szybkie i częste publikowanie nowych wersji aplikacji, co pozwala szybko reagować na błędy i wprowadzać nowe funkcje.

**Dokumentacja** – zarówno dla użytkowników końcowych, jak i dla deweloperów, aby ułatwić dalszy rozwój oraz użytkowanie oprogramowania.

**Refaktoryzacja** – regularna poprawa istniejącego kodu bez zmiany jego funkcjonalności, co pozwala na optymalizację i uproszczenie kodu, co w dłuższym okresie ułatwia jego utrzymanie.

**Zasada SOLID** – pięć zasad: 
- pojedyncza odpowiedzialność (Single Responsibility), 
- otwarte-zamknięte (Open-Closed), 
- zastępowalność Liskov (Liskov Substitution), 
- segregacja interfejsów (Interface Segregation)
- odwrócenie zależności (Dependency Inversion),
 które pomagają w tworzeniu elastycznego i skalowalnego kodu obiektowego.

Wzorce projektowe –  Singleton, Factory, Observer,

**User-centered design (UCD)** – projektowanie z uwzględnieniem potrzeb użytkownika końcowego, dzięki czemu oprogramowanie jest bardziej intuicyjne i dostosowane do oczekiwań użytkownika.

**Utrzymanie jakości kodu** – przegląd kodu, analizy statyczne, np. SonarQube, linters i inne narzędzia do zapewnienia wysokiej jakości kodu.

> zasady wygenerowane przez chatgpr4o

**Kodowanie i dokumentacja ręczne** –  piszemy ręcznie wyjaśnienie każdej funkcji w pliku [Readme](README.md) tam by każdy zrozumiał  co do czego służy. 

# UwuBiś aplikacja do ćwiczenia słuchu. 
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

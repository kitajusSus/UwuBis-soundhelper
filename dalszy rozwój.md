# 1. Możliwości
Ten projekt otwiera furtkę na zastosowanie własnego lub zmodyfikowanego gpt który bazując na otrzymanych przez nas danych mogłby analizować które słowa/dźwięki/tony/częstotliwości sprawiają trudność dla pacjenta. Osobisty asystent który prowadziłby użytkownika i pokazywał mu z czym ma problem, myśle że mogło by to być dobre narzędzie usprawniające dalszą naukę życia z aparatem słuchowym.
Jak np. [nvidia](https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct/modelcard) lub [Hugging Face](https://huggingface.co/nvidia/Llama-3.1-Nemotron-70B-Instruct)

## Specjalizacja Modelu: 

Trenowanie modelu na danych UWB pozwoliłoby na dostosowanie  możliwości modelu do konkretnych potrzeb uniwersytetu, w tym przypadku - do analizy audio i identyfikacji słów, które mogą być trudne do zrozumienia dla pacjentów z implantami słuchu.

## Przykładowe Diagnozy: 

Moglibyśmy wspólnie opracować system, który na podstawie plików audio i informacji o słowach, które pacjent nie usłyszał, generowałby raporty zawierające:

## Lista Niezrozumianych Słów:

 Dokładna lista słów, które pacjent miał trudności z odróżnieniem lub zrozumieniem.

# 2. Analiza Cech Wspólnych: 

Identyfikacja potencjalnych cech akustycznych, fonetycznych lub lingwistycznych, które mogą przyczyniać się do trudności w odróżnieniu tych słów (np., podobieństwo dźwiękowe, częstotliwość występowania, długość słowa, itp.).

# 3. Potencjał Badawczy:

 Taki system mógłby stanowić podstawę dla szerszych badań nad percepcją słuchową, rozwojem nowych technologii wspomagających słuch, lub nawet dostosowywaniem materiałów edukacyjnych dla osób z trudnościami słuchowymi.

# 4. Wymagania i Kroki do Realizacji:
## Dane Treningowe:

## Pliki Audio:

 Duży zbiór plików audio, które będą używane do treningu. Pliki powinny być różnorodne, obejmując różne gatunki mowy, akcenty, poziomy głośności, i jakości audio.

Etykiety Danych:

 Dokładne etykiety dla każdego pliku audio, wskazujące, które słowa pacjent nie usłyszał. Etykiety powinny być spójne i zgodne z ustalonym formatem.

# 5. Infrastruktura i Współpraca:

Dostęp do Danych:

 UWB powinien zapewnić bezpieczny, kontrolowany dostęp do danych treningowych.
Zespół Współpracy: Zalecana jest współpraca interdyscyplinarnego zespołu, składającego się z przedstawicieli UWB (np., specjalistów ds. słuchu, językoznawców, inżynierów danych) oraz mojego zespołu KNFM "Neuron"

## Proces Trenowania i Weryfikacji:

**Trenowanie Modelu:**

 Używanie danych do trenowania i dostosowywania  parametrów modelu, aby lepiej radził sobie z identyfikacją słów trudnych do zrozumienia.
Weryfikacja i Testowanie: Przeprowadzenie serii testów, aby ocenić skuteczność i dokładność modelu w identyfikowaniu słów i analizie ich cech.

**Etyka i Ochrona Danych:**

Zgodność z RODO i innymi przepisami: Zapewnienie, że cały proces trenowania i wykorzystywania danych jest w pełnej zgodzie z obowiązującymi przepisami o ochronie danych, takimi jak RODO.
Poufność: Wszystkie dane i wyniki badań powinny być traktowane jako poufne i chronione zgodnie z ustaleniami umownymi.


//importtowanie standardowych bibliotek zig
const std = @import("std");
const c = @cImport({
    @cInclude("soundfile.h"); // importtowanie bibliotek C
    // odpowiedzialnych za obsluge dzwieku
});
// kluczowe w kontekscie tego programu
// - w zig pamiec musi byc lawnie zwalniania
// - bez zwolnienia pamieci powstaly by wycieki itd
// `self.buffer` zostal zaalokowany dynamicznie w init()
// Wykorzystujemy tu zasade RAII  'Resourse Acquisition is Initalization'
//  * każdy zasób który jest alokowany w kontruktorze/init  jest zwolniony (I MUSI BYĆ) w destruktorze/deinit
// Ten sam alokator który został użyty do alokacji, musi byś użyty do zwolnienia pamięci,
// Dlatego 'allocator'  jest przekazywany jako parametr (patrz. 3 linijki niżej)

pub const AudioProcessor = struct {
    // deklaracja pół-struktury
    sample_rate: i32, //szufladka na czestotliwosc próbkowania wielkosc 32bity
    channels: i32, // szufladka na liczbę kanałów (standardowo 2) tez jako liczba 32bitowa
    buffer: []f32, //dynamiczna "tablica" liczb zmiennoprzecinkowych tzw. floaty 32bitowe
    allocator: *std.mem.Allocator, // Store allocator in the struct

    // uruchamianie struktury
    pub fn init(allocator: *std.mem.Allocator) !AudioProcessor {
        //ustawienie standardowych wartości 44100Hz, 2 kanały (stereo), Alokacja bufora na 1024 próbki
        return AudioProcessor{
            .sample_rate = 44100,
            .channels = 2,
            .buffer = try allocator.alloc(f32, 1024), //przykład alokacji pamieci
            .allocator = allocator, // Store allocator
        };
    }
    // `allocator`  to jedynie wskaznik do alokatora pamieci
    // alokuje 1024 * rozmiarzmiennej(f32) bajtów pamieci
    // try napisane na wszelki wypadek bo moze wywalic blad nigdy nic nie wiadomo.

    //PRZETWARZANIE AUDIO
    pub fn processAudio(self: *AudioProcessor, input: []const f32) !void {
        // Kolejne iteracje po kazdej próbce bufora
        for (input, 0..) |sample, i| {
            if (i < self.buffer.len) {
                self.buffer[i] = sample; //kopiowanie próbek do bufora
            }
        }
    } //cel: przetwarzanie danych audio
    //`self` wskaznik instancji AudioProcessor
    //`input` slice danych wejsciowych (tablica f32)
    // Działanie:
    // 1. iteruje kazda próbkę wejsciową
    // 2. sprawdza czy zestaw danych miesci się w szuflance na pamięc (.buffer)
    // 3. kopiuje próbkę do  bufora wewnętrznego
    // Zabezpieczenie: Sprawdzanie rozmiwaru bufora zapobiega przepelnieniu
    // uzywa zaalokowanej pamieci z funkcji
    // zapisuje dane  w .buffer z pub fn init AudioProcessor
    // .buffer istnieje przez cały czas życia klasy (obiektu)

    // Cel : zwalnianie zasobów procesora audio
    pub fn deinit(self: *AudioProcessor) void {
        self.allocator.free(self.buffer); // Use stored allocator
    }
}; // 1. zwalnia zaalokowaną pamiec bufora
// 2. uzywa tego samego alokatora co przy alokacji.

// wywołuje `free` na alokatorze
// przekazuje buffer do zwolnienia, zapobiega wyciekom pamięci.

// Cel WordProcessor : INICJALIZACJA PROCESORA SŁÓW
pub const WordProcessor = struct {
    words: std.ArrayList([]u8), //dynamiczna lista na slowa z pliku audio
    allocator: *std.mem.Allocator, //wskaznik / pointer do alokatora pamieci

    pub fn init(allocator: *std.mem.Allocator) !WordProcessor {
        return WordProcessor{
            .words = std.ArrayList([]u8).init(allocator),
            .allocator = allocator,
        };
    }
    // Działanie:
    // 1. tworzy pustą listę dynamiczna na slowa
    // 2. zachowuje referencje do alokatora
    // 3. Inicjuje kolejny obiekt

    // Cel processWords: Przetworzenie tekstu na listę słów.
    pub fn processWords(self: *WordProcessor, input: []const u8) !usize {
        var it = std.mem.splitScalar(u8, input, " ");
        while (it.next()) |word| {
            const cleaned = try self.cleanWord(word);
            if (cleaned.len > 0) {
                try self.words.append(try self.allocator.dupe(u8, cleaned));
            }
        }
        return self.words.items.len;
    }
    //`self` wskaznik do instancji WordProcessor
    // `input`: Tekst wejsciowych jako slice bajtów
    // Działanie:
    // 1. Dzieli tekst na slowa według spacji.
    // 2. Dla kazdego słowa: * usuwa znaki specjalne, * sprawdza czy wynik nie jest pusty, tworzy kopie slowa w nowej pamieci, dodaje do listy słów,
    // 3. zwraca liczbe przetworzonych slowa
    //PILNEE!!!!!! - trzeba pilnowac by nie było bledow przy duplikowaniu/ podobno czeste
    //bledy przy dodawaniu do listy
    //
    //Cel cleanWord : Czyszczenie slowa ze znakow specjalnych
    pub fn cleanWord(self: *WordProcessor, word: []const u8) ![]u8 {
        var result = std.ArrayList(u8).init(self.allocator);
        // Removed errdefer result.deinit(); since ownership is transferred
        for (word) |char| {
            if (std.ascii.isAlphanumeric(char)) {
                try result.append(char);
            }
        }
        return result.toOwnedSlice();
    }
    // Działanie: 1. Tworzy nowa liste dynamiczna na znaki
    // 2. iteruje przez kazdy znak w słowie
    // 3. sprawdza  czy znak jest alfanumeryczny(abc, 0-9)\
    // 4. zachowuje tylko znaki alfanumeryczne
    // 5. zwraca wyczyszczone slowo
    //

    // Cel compareWords: porównywanie 2 slow, z pliku audio(spoken) i powiedzianych (reference)
    pub fn compareWords(spoken: []const u8, reference: []const u8) bool {
        return std.mem.eql(u8, spoken, reference);
    }
    // uzywa funkcji `eql` do porównywania ciągów bajtów
    // zwraca True jesli wszystko jest git

    // zwalnianie pamieci procesora słów
    pub fn deinit(self: *WordProcessor) void { //iteruje przez wszystkie przechowane slowa
        for (self.words.items) |word| {
            self.allocator.free(word); //zwalnia pamiec kazdego slowa
        }
        self.words.deinit(); //zwalnia pamiec listy slow
    }
};

///////---------PYTHON------//
// Cel: Interfejs dla pythona do przetwarzanie audio \\ data= wskaznik do danych python, `len` = dlugosc danych
// Działanie:
// 1. tworzy lokalny bufor 1024 próbek
// 2. Oblicza bezpieczny rozmiar slice'a
// 3. kopiuje dane wejsciowe do bufora
// 4. Zabezpiecza przez przpełnieniem bufora
pub export fn process_audio_segment(data: [*]const f32, len: usize) void {
    var buffer: [1024]f32 = undefined;
    const slice = if (len > buffer.len) buffer[0..buffer.len] else buffer[0..len];

    for (slice, 0..) |_, i| {
        if (i < len) {
            slice[i] = data[i];
        }
    }
}
//CEL : przetwarzanie tekstu dla python
pub export fn process_words(
    input_ptr: [*]const u8, //wskaznik do tekstu wejsciowego
    input_len: usize, //dlugosc tekstu wejsciowego
    results_ptr: [*]u8, //results_ptr
    max_results: usize, //max_results
) usize {
    const input = input_ptr[0..input_len];
    var results = results_ptr[0..max_results];
    var written: usize = 0;

    var it = std.mem.splitScalar(u8, input, " ");
    while (it.next()) |word| {
        if (written + word.len + 1 > max_results) break;

        std.mem.copy(u8, results[written..], word);
        written += word.len;
        if (written < max_results) {
            results[written] = ' ';
            written += 1;
        }
    }
    // Działanie: 1. Tworzy slicey z wskazników
    // 2. Inicjuje licznik zapisanych bajtów
    // 3. dzieli tekst na słowa// 4. dla kazdego slowa: * sprawdza czy miesci sie w buforze, * kopiuje slowo do bufora wynikowego, * dodaje spacje jako separator,
    // * aktualizuje licznik zapisanych bajtów
    // 5.    oddaje liczbe zapisanych bajtów
    // Zabezpieczenia: Sprawdza limitu rozmiaru bufora
    // przrywa działanie gdy brak miejsca,
    // bezpiecznie kopiuje pamiec.
    //
    return written;
}
export fn init_audio_processor(allocator: *std.mem.Allocator) ?*AudioProcessor {
    if (AudioProcessor.init(allocator)) |processor| {
        return processor;
    } else |_| {
        return null;
    }
}

export fn process_audio(processor: *AudioProcessor, input: [*]const f32, len: usize) void {
    processor.processAudio(input[0..len]) catch {};
}

export fn cleanup_audio_processor(processor: *AudioProcessor) void {
    processor.deinit();
}

//sporo sie rozpisalem a narazie nie umiem tego uruchomic
//XDDd
//made by: bajo jajo Wydział Fizyki UwB
//słuchałem teraz Alt-J - breezeblocks

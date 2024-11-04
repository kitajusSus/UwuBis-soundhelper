const std = @import("std");
const os = std.os;
const fs = std.fs;
const time = std.time;
const Allocator = std.mem.Allocator;
const ArrayList = std.ArrayList;

const GUI = @import("zig-gui");

const App = struct {
    root: GUI.Window,
    login: []const u8,
    wynik: []const u8,
    czas_start: time.Time,
    folder_zapisu: []const u8 = "wyniki/",
    katalog_audio: []const u8 = "audio/demony/",
    ile_slow_do_rozpoznania: usize = 5,
    plik_audio: []const u8,
    słowa_w_pliku: ArrayList([]const u8),
    rozdziały: ArrayList([]const u8),
    wyniki_użytkownika: std.HashMap([]const u8, []const u8),
    ekrany: ArrayList(GUI.Widget),
    aktualny_ekran: ?GUI.Widget = null,
    current_chapter: usize = 0,

    pub fn init(allocator: *Allocator) !App {
        return App{
            .root = try GUI.Window.init(allocator, "Aplikacja UwuBiś", 800, 600),
            .login = "",
            .wynik = "",
            .czas_start = try time.Time.now(),
            .plik_audio = "",
            .słowa_w_pliku = try ArrayList([]const u8).init(allocator),
            .rozdziały = try ArrayList([]const u8).init(allocator),
            .wyniki_użytkownika = std.HashMap([]const u8, []const u8).init(allocator),
            .ekrany = try ArrayList(GUI.Widget).init(allocator),
        };
    }

    pub fn login_screen(self: *App) void {
        if (self.aktualny_ekran) |ekran| {
            self.ekrany.append(ekran) catch {};
            ekran.hide();
        }

        const frame = GUI.Frame.init(self.root);
        frame.add(GUI.Label.init("Login:"));
        frame.add(GUI.TextBox.init(&self.login));
        frame.add(GUI.Button.init("Zaloguj się", self.sprawdź_login));
        frame.add(GUI.Button.init("Cofnij", self.cofnij));
        self.aktualny_ekran = frame;
        frame.show();
    }

    pub fn sprawdź_login(self: *App) void {
        if (std.mem.eql(u8, self.login, "test")) {
            self.wybierz_folder_audio_screen();
        } else {
            GUI.MessageBox.error("Błąd", "Niepoprawny login");
        }
    }

    pub fn wybierz_folder_audio_screen(self: *App) void {
        if (self.aktualny_ekran) |ekran| {
            self.ekrany.append(ekran) catch {};
            ekran.hide();
        }

        const frame = GUI.Frame.init(self.root);
        frame.add(GUI.Button.init("Wybierz folder z plikami audio", self.wybierz_folder_audio));
        frame.add(GUI.Button.init("Cofnij", self.cofnij));
        self.aktualny_ekran = frame;
        frame.show();
    }

    pub fn wybierz_folder_audio(self: *App) void {
        const folder = GUI.FileDialog.openFolder();
        if (folder) |path| {
            self.katalog_audio = path;
            self.pliki_audio_screen();
        } else {
            GUI.MessageBox.error("Błąd", "Nie wybrano folderu");
        }
    }

    pub fn pliki_audio_screen(self: *App) void {
        if (self.aktualny_ekran) |ekran| {
            self.ekrany.append(ekran) catch {};
            ekran.hide();
        }

        const frame = GUI.Frame.init(self.root);
        const listbox = GUI.ListBox.init();
        const dir = try fs.Dir.open(self.katalog_audio);
        defer dir.close();

        var it = try dir.iterate();
        while (try it.next()) |entry| {
            if (std.mem.endsWith(u8, entry.name, ".wav")) {
                listbox.add(entry.name);
            }
        }

        if (listbox.len() == 0) {
            GUI.MessageBox.error("Błąd", "Brak plików audio w wybranym folderze");
            self.cofnij();
            return;
        }

        frame.add(listbox);
        frame.add(GUI.Button.init("Wybierz plik audio", self.wybierz_plik_audio));
        frame.add(GUI.Button.init("Cofnij", self.cofnij));
        self.aktualny_ekran = frame;
        frame.show();
    }

    pub fn wybierz_plik_audio(self: *App) void {
        const listbox = self.aktualny_ekran.?.getListBox();
        if (listbox) |lb| {
            self.plik_audio = lb.getSelected();
            self.słowa_w_pliku = try rozpoznaj_slowa_z_pliku(self.plik_audio, self.ile_slow_do_rozpoznania);
            self.rozdziały = try self.słowa_w_pliku.split(self.ile_slow_do_rozpoznania);
            self.rozdziały_screen();
        } else {
            GUI.MessageBox.error("Błąd", "Nie wybrano pliku audio");
        }
    }

    pub fn rozdziały_screen(self: *App) void {
        if (self.aktualny_ekran) |ekran| {
            self.ekrany.append(ekran) catch {};
            ekran.hide();
        }

        const frame = GUI.Frame.init(self.root);
        const listbox = GUI.ListBox.init();
        for (self.rozdziały.items) |rozdział, i| {
            listbox.add("Rozdział " ++ std.fmt.format("{d}: {s}", .{i + 1, rozdział}));
        }

        frame.add(listbox);
        frame.add(GUI.Button.init("Wybierz rozdział", self.wybierz_rozdział));
        frame.add(GUI.Button.init("Cofnij", self.cofnij));
        self.aktualny_ekran = frame;
        frame.show();
    }

    pub fn wybierz_rozdział(self: *App) void {
        const listbox = self.aktualny_ekran.?.getListBox();
        if (listbox) |lb| {
            const wybrany_rozdział = lb.getSelected();
            const numer_rozdziału = std.fmt.parseInt(usize, wybrany_rozdział.split(":")[0].split(" ")[1]) - 1;
            const słowa_w_rozdziale = self.rozdziały[numer_rozdziału];
            if (self.wyniki_użytkownika.get(numer_rozdziału)) |wynik| {
                self.wynik = wynik;
            } else {
                self.wynik = "Brak wyniku";
            }
            self.przebieg_testu(numer_rozdziału);
        } else {
            GUI.MessageBox.error("Błąd", "Nie wybrano rozdziału");
        }
    }

    pub fn przebieg_testu(self: *App, numer_rozdziału: usize) void {
        self.current_chapter = numer_rozdziału;
        self.aktualny_ekran.?.hide();
        odtwarzaj_audio(self.plik_audio);
        std.time.sleep(1 * std.time.ns_per_s);

        const frame = GUI.Frame.init(self.root);
        frame.add(GUI.Label.init("Powtórz słowa które usłyszałeś"));
        const (poprawne_slowa, powtórzone_słowa) = powtorz_słowa(self.rozdziały[numer_rozdziału]);
        const wynik = std.fmt.format("{d}/{d}", .{poprawne_slowa.len(), self.rozdziały[numer_rozdziału].len()});
        self.wyniki_użytkownika.put(numer_rozdziału, wynik);
        self.zapytaj_o_dalsze(numer_rozdziału, wynik, poprawne_slowa, powtórzone_słowa, self.rozdziały[numer_rozdziału]);
    }

    pub fn zapytaj_o_dalsze(self: *App, numer_rozdziału: usize, wynik: []const u8, poprawne_słowa: []const u8, powtórzone_słowa: []const u8, słowa_w_rozdziale: []const u8) void {
        if (self.aktualny_ekran) |ekran| {
            self.ekrany.append(ekran) catch {};
            ekran.hide();
        }

        const frame = GUI.Frame.init(self.root);
        frame.add(GUI.Label.init("Wynik: " ++ wynik));
        zapisz_wynik(self.login, self.plik_audio, słowa_w_rozdziale, powtórzone_słowa, wynik, self.folder_zapisu);
        self.wyświetl_statystyki(słowa_w_rozdziale, poprawne_słowa, powtórzone_słowa);
        frame.add(GUI.Button.init("Wybierz kolejny rozdział", self.rozdziały_screen));
        frame.add(GUI.Button.init("Cofnij", self.cofnij));
        self.aktualny_ekran = frame;
        frame.show();
    }

    pub fn cofnij(self: *App) void {
        if (self.ekrany.len() > 0) {
            self.aktualny_ekran.?.hide();
            self.aktualny_ekran = self.ekrany.pop();
            self.aktualny_ekran.?.show();
        }
    }

    pub fn wyświetl_statystyki(self: *App, słowa_w_rozdziale: []const u8, poprawne_słowa: []const u8, powtórzone_słowa: []const u8) void {
        const frame = GUI.Frame.init(self.root);
        const text = GUI.TextBox.init();
        text.setText("Poprawnie powtórzone słowa: " ++ std.fmt.format("{d}/{d}", .{poprawne_słowa.len(), słowa_w_rozdziale.len()}) ++ "\n");
        for (słowo, powtórzone) in std.mem.zip(słowa_w_rozdziale, powtórzone_słowa) {
            text.appendText(std.fmt.format("{s} -> {s}\n", .{słowo, powtórzone}));
        }
        frame.add(text);
        frame.add(GUI.Button.init("Odtwórz to samo audio", self.powtórz_audio));
        frame.add(GUI.Button.init("Dalej", self.odtwórz_kolejny_audio));
        frame.add(GUI.Button.init("Zakończ", self.root.close));
        frame.add(GUI.Button.init("Cofnij", self.wybierz_folder_audio_screen));
        self.aktualny_ekran = frame;
        frame.show();
    }

    pub fn powtórz_audio(self: *App) void {
        self.root.close();
        self.przebieg_testu(self.current_chapter);
    }

    pub fn odtwórz_kolejny_audio(self: *App) void {
        self.current_chapter += 1;
        if (self.current_chapter < self.rozdziały.len()) {
            self.root.close();
            self.przebieg_testu(self.current_chapter);
        } else {
            GUI.MessageBox.info("Koniec", "To był ostatni rozdział.");
        }
    }
};

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    var app = try App.init(allocator);
    app.login_screen();
    app.root.run();
}

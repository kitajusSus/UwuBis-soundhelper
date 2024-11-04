const std = @import("std");
const fs = std.fs;
const Allocator = std.mem.Allocator;
const ArrayList = std.ArrayList;

pub fn zapisz_wynik(allocator: *Allocator, login: []const u8, nazwa_audio: []const u8, poprawne_słowa: []const u8, powtórzone_słowa: []const u8, słowa: []const u8, folder_zapisu: []const u8) !void {
    const nazwa_pliku = fs.path.join(allocator, folder_zapisu, login ++ ".xlsx") catch return;
    if (!fs.path.exists(nazwa_pliku)) {
        const file = try fs.File.create(nazwa_pliku, .{});
        defer file.close();
        try file.writeAll("Numer podejścia,Nazwa Pliku i rozdział,Słowa w pliku,Słowa poprawne,Słowa niepoprawne,Wynik,Maksymalny Wynik\n");
    }

    const file = try fs.File.open(nazwa_pliku, .{ .append = true });
    defer file.close();

    const niepoprawne_słowa = try ArrayList([]const u8).init(allocator);
    defer niepoprawne_słowa.deinit();
    for (słowo in słowa) {
        if (!std.mem.contains(poprawne_słowa, słowo)) {
            try niepoprawne_słowa.append(słowo);
        }
    }

    const wynik = std.fmt.format("{d}/{d}", .{poprawne_słowa.len(), słowa.len()});
    const maks_wynik = std.fmt.format("{d}", .{słowa.len()});
    const new_row = std.fmt.format("{d},{s},{s},{s},{s},{s},{s}\n", .{
        file.getSize() / 1024,
        nazwa_audio,
        std.mem.join(", ", słowa),
        std.mem.join(", ", poprawne_słowa),
        std.mem.join(", ", niepoprawne_słowa.items),
        wynik,
        maks_wynik,
    });
    try file.writeAll(new_row);
}

pub fn rozpoznaj_slowa_z_pliku(allocator: *Allocator, nazwa_pliku: []const u8, ile_slow_do_rozpoznania: usize) !ArrayList([]const u8) {
    const r = try sr.Recognizer.init(allocator);
    const source = try sr.AudioFile.open(nazwa_pliku);
    defer source.close();

    const audio = try r.record(source);
    const text = try r.recognize_google(audio, "pl-PL");
    const słowa = try ArrayList([]const u8).init(allocator);
    for (word in text.split(" ")) |słowo| {
        if (słowa.len() < ile_slow_do_rozpoznania) {
            try słowa.append(słowo);
        }
    }
    return słowa;
}

pub fn powtorz_słowa(allocator: *Allocator, słowa: []const u8) !([]const u8, []const u8) {
    const r = try sr.Recognizer.init(allocator);
    const source = try sr.Microphone.open();
    defer source.close();

    const audio = try r.listen(source, 10);
    const powtórzone_słowa = try r.recognize_google(audio, "pl-PL").split(" ");
    const poprawne_słowa = try ArrayList([]const u8).init(allocator);
    for (słowo in słowa) {
        if (std.mem.contains(powtórzone_słowa, słowo)) {
            try poprawne_słowa.append(słowo);
        }
    }
    return (poprawne_słowa.items, powtórzone_słowa);
}

pub fn odtwarzaj_audio(nazwa_pliku: []const u8) !void {
    const data = try sf.read(nazwa_pliku);
    try sd.play(data);
    try sd.wait();
}

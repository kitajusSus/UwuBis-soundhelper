const std = @import("std");

pub fn build(b: *std.Build) void {
    // Utwórz obiekt współdzielonej biblioteki
    const lib = b.addSharedLibrary(.{
        .name = "audio",
        // Użyj .root_source_file zamiast .path
        .root_source_file = .{ .cwd_relative = "zig_audio.zig" },
        // Dodaj wersję jeśli jest wymagana
        .version = .{ .major = 0, .minor = 0, .patch = 1 },
        // Dodaj docelową platformę
        .target = b.standardTargetOptions(.{}),
        // Dodaj tryb optymalizacji
        .optimize = b.standardOptimizeOption(.{}),
    });

    // Linkowanie z biblioteką C
    lib.linkLibC();

    // Dodaj ścieżkę include
    lib.addIncludePath(.{ .cwd_relative = "include" });

    // Instalacja artefaktu
    b.installArtifact(lib);
}

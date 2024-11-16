const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib = b.addSharedLibrary(.{
        .name = "audio",
        .root_source_file = .{ .path = "zig_audio.zig" },
        .target = b.standardTargetOptions(.{}),
        .optimize = .ReleaseSafe,
    });

    lib.linkLibC();
    lib.addIncludePath(.{ .cwd_relative = "include" });

    // Use installArtifact instead of install
    b.installArtifact(lib);
}

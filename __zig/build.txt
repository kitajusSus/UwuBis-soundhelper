const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const audio_lib = b.addSharedLibrary(.{
        .name = "audio_library",
        .root_source_file = b.path("audio.zig"),
        .target = target,
        .optimize = optimize,
        .version = .{ .major = 1, .minor = 0, .patch = 0 },
    });

    b.installArtifact(audio_lib);
}

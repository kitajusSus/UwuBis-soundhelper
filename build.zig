const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib = b.addSharedLibrary(.{
        .name = "audio",
        .root_source_file = .{ .cwd_relative = "src/backend/zig_audio.zig" },
        .target = target,
        .optimize = optimize,
        .version = .{ .major = 0, .minor = 1, .patch = 0 },
    });

    lib.linkLibC();
    lib.addIncludePath(.{ .cwd_relative = "include" });

    // Use installArtifact instead of install
    b.installArtifact(lib);
}

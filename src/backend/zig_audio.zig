const std = @import("std");
const c = @cImport({
    @cInclude("soundfile.h");
});

pub const AudioProcessor = struct {
    sample_rate: i32,
    channels: i32,
    buffer: []f32,

    pub fn init(allocator: *std.mem.Allocator) !AudioProcessor {
        return AudioProcessor{
            .sample_rate = 44100,
            .channels = 2,
            .buffer = try allocator.alloc(f32, 1024),
        };
    }

    pub fn processAudio(self: *AudioProcessor, input: []const f32) !void {
        // Implement audio processing logic here [TO DO ]
        for (input, 0..) |sample, i| {
            if (i < self.buffer.len) {
                self.buffer[i] = sample;
            }
        }
    }

    pub fn deinit(self: *AudioProcessor, allocator: *std.mem.Allocator) void {
        allocator.free(self.buffer);
    }
};

pub const WordProcessor = struct {
    words: std.ArrayList([]u8),
    allocator: *std.mem.Allocator,

    pub fn init(allocator: *std.mem.Allocator) !WordProcessor {
        return WordProcessor{
            .words = std.ArrayList([]u8).init(allocator),
            .allocator = allocator,
        };
    }

    pub fn processWords(self: *WordProcessor, input: []const u8) !usize {
        var it = std.mem.split(u8, input, " ");
        while (it.next()) |word| {
            const cleaned = try self.cleanWord(word);
            if (cleaned.len > 0) {
                try self.words.append(try self.allocator.dupe(u8, cleaned));
            }
        }
        return self.words.items.len;
    }

    pub fn cleanWord(self: *WordProcessor, word: []const u8) ![]u8 {
        var result = std.ArrayList(u8).init(self.allocator);
        for (word) |char| {
            if (std.ascii.isAlphanumeric(char)) {
                try result.append(char);
            }
        }
        return result.toOwnedSlice();
    }

    pub fn compareWords(spoken: []const u8, reference: []const u8) bool {
        return std.mem.eql(u8, spoken, reference);
    }

    pub fn deinit(self: *WordProcessor) void {
        for (self.words.items) |word| {
            self.allocator.free(word);
        }
        self.words.deinit();
    }
};
//
pub export fn process_audio_segment(data: [*]const f32, len: usize) void {
    var buffer: [1024]f32 = undefined;
    const slice = if (len > buffer.len) buffer[0..buffer.len] else buffer[0..len];

    for (slice, 0..) |_, i| {
        if (i < len) {
            slice[i] = data[i];
        }
    }
}

pub export fn process_words(
    input_ptr: [*]const u8,
    input_len: usize,
    results_ptr: [*]u8,
    max_results: usize,
) usize {
    const input = input_ptr[0..input_len];
    var results = results_ptr[0..max_results];
    var written: usize = 0;

    var it = std.mem.split(u8, input, " ");
    while (it.next()) |word| {
        if (written + word.len + 1 > max_results) break;

        std.mem.copy(u8, results[written..], word);
        written += word.len;
        if (written < max_results) {
            results[written] = ' ';
            written += 1;
        }
    }

    return written;
}

const std = @import("std");

pub const Error = error{ FileOpenFailed, AllocationFailed };

pub fn segment_audio(
    filename: [*]const u8,
    sample_rate: *u32,
    segments: [][]u8,
    num_segments: *usize,
) !void {
    const allocator = std.heap.page_allocator;

    // Open file
    var file = try std.fs.cwd().openFile(filename, .{ .read = true });
    defer file.close();

    // Read file size
    const file_size = try file.getEndPos();

    // Read audio data
    const data = try allocator.alloc(u8, file_size);
    defer allocator.free(data);
    try file.readAll(data);

    // Calculate segment size
    const segment_duration = 5; // seconds
    const samples_per_segment = segment_duration * sample_rate.*;
    const total_segments = data.len / samples_per_segment;

    // Create segments
    var start = 0;
    for (segments.len) |idx| {
        const end = start + samples_per_segment;
        const segment = try allocator.alloc(u8, end - start);
        defer allocator.free(segment);

        std.mem.copy(u8, segment, data[start..end]);
        segments[idx] = segment;
        start = end;
    }

    num_segments.* = total_segments;
}

// load_audio: Wczytuje plik audio i zwraca zawartość w postaci tablicy bajtów.
// free_audio: Zwalnia alokowaną pamięć, po zakończeniu pracy z danymi audio.
// Powyższy kod wczytuje plik audio i zwraca jego zawartość w formie dynamicznej tablicy bajtów.
// Będziemy musieli przechować zawartość tego pliku w pamięci,
//aby móc pracować z jego danymi w Pythonie.

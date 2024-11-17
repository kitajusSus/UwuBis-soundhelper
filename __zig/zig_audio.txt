import ctypes

def segment_audio(file_path, sample_rate):
    """
    Funkcja wywołująca Zig do segmentacji audio.
    """
    lib = ctypes.CDLL('./audio_library.so')  # Ścieżka do biblioteki Zig

    lib.segment_audio.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32),
                                  ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
                                  ctypes.POINTER(ctypes.c_size_t)]
    lib.segment_audio.restype = ctypes.c_int

    sample_rate = ctypes.c_uint32(sample_rate)
    segments = ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8))()
    num_segments = ctypes.c_size_t(0)

    result = lib.segment_audio(
        file_path.encode('utf-8'),
        ctypes.byref(sample_rate),
        ctypes.byref(segments),
        ctypes.byref(num_segments)
    )

    if result != 0:
        raise RuntimeError("Failed to segment audio")

    return segments, num_segments.value
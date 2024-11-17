import ctypes
import numpy as np
from pathlib import Path
from library import AUDIOLIB
import logging


class ZigAudioProcessor:
    def __init__(self):
        lib_path = Path(__file__).parent / "zig-out" / "lib" / "audio.dll"
        logging.info(f"Looking for DLL at: {lib_path}")
        
        if not lib_path.exists():
            logging.error(f"DLL not found at {lib_path}")
            logging.info(f"Current directory: {Path.cwd()}")
            raise FileNotFoundError(f"DLL not found at {lib_path}")
            
        try:
            self.lib = ctypes.CDLL(str(lib_path))
            logging.info("DLL loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load DLL: {e}")
            raise
        # Definicje typów
        self.lib.init_audio_processor.restype = ctypes.c_void_p
        self.lib.process_audio.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
        
        # Inicjalizacja
        self.processor = self.lib.init_audio_processor()
        if not self.processor:
            raise RuntimeError("Failed to initialize audio processor")

    def __del__(self):
        if hasattr(self, 'processor') and self.processor:
            self.lib.cleanup_audio_processor(self.processor)

    def process_segment(self, audio_data: np.ndarray):
        """Process audio segment using Zig implementation"""
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        self.lib.process_audio_segment(audio_data, len(audio_data))
        return audio_data

class WordProcessor:
    def __init__(self):
        lib_path = Path(__file__).parent / "zig-out/lib/audio.dll"
        self.lib = ctypes.CDLL(str(lib_path))
        
        # Configure function signatures
        self.lib.process_words.argtypes = [
            ctypes.c_char_p,
            ctypes.c_size_t,
            ctypes.c_char_p,
            ctypes.c_size_t
        ]
        self.lib.process_words.restype = ctypes.c_size_t

    def process_words(self, text: str, max_results: int = 1024) -> list[str]:
        text_bytes = text.encode('utf-8')
        result_buffer = ctypes.create_string_buffer(max_results)
        
        written = self.lib.process_words(
            text_bytes,
            len(text_bytes),
            result_buffer,
            max_results
        )
        
        if written > 0:
            result_str = result_buffer.value[:written].decode('utf-8')
            return [w for w in result_str.split() if w]
        return []

class AudioProcessor:
    def __init__(self, config):
        self.config = config
        self.audio_lib = AUDIOLIB(config)
        self.zig_processor = ZigAudioProcessor()
        self.word_processor = WordProcessor()
    
    def process_audio_file(self, file_path):
        """Process audio file using both Python and Zig"""
        # Standard processing
        result = self.audio_lib.load_audio_file(file_path)
        
        # Additional Zig processing for performance critical parts
        if result and hasattr(self.audio_lib, 'current_segment_data'):
            self.audio_lib.current_segment_data = \
                self.zig_processor.process_segment(self.audio_lib.current_segment_data)
        
        return result

    def process_segment(self, segment_words: list[str]) -> list[str]:
        """Process words in segment using Zig implementation"""
        text = " ".join(segment_words)
        return self.word_processor.process_words(text)

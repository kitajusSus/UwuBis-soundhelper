import sys
import logging
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.config.settings import load_config

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    setup_logging()
    logging.info("Starting application...")
    
    app = QApplication(sys.argv)
    try:
        config = load_config()
    except Exception as e:
        logging.warning(f"Failed to load config: {e}, using defaults")
        config = None
        
    window = MainWindow(config)
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
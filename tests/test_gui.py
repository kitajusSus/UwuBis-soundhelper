
import pytest
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.config.settings import load_config

@pytest.fixture
def app():
    return QApplication([])

@pytest.fixture
def window(app):
    config = load_config()
    return MainWindow(config)

def test_window_title(window):
    assert window.windowTitle() == 'UwuBiś'

def test_initial_state(window):
    assert window.login == ""
    assert window.current_segment == 0
    assert window.total_segments == 0

def test_login_validation(window):
    window.login_input.setText("")
    window.handleLogin()
    assert window.login == ""
    
    window.login_input.setText("test")
    window.handleLogin()
    assert window.login == "test"

def test_audio_selection(window, mocker):
    # Mock file dialog
    mocker.patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory', 
                 return_value="/test/audio")
    window.selectAudioFolder()
    assert window.katalog_audio == "/test/audio"
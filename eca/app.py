from .ui_manager import UIManager
from .gaze_tracker import GazeTracker
from .voice_engine import VoiceEngine
from .settings import Settings
from .logger import Logger
from .command_engine import CommandEngine
from .ui_manager import UIManager

class ECAApp:
    def __init__(self):
        self.settings = Settings()
        self.logger = Logger()
        self.gaze = GazeTracker(self.settings, self.logger)
        self.voice = VoiceEngine(self.settings, self.logger)
        self.command_engine = CommandEngine(self.logger)
        self.ui = UIManager(self.settings, self.gaze, self.voice, self.command_engine, self.logger)

    def run(self):
        self.ui.start()

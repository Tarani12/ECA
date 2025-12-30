import threading, time
import speech_recognition as sr

class VoiceEngine:
    def __init__(self, settings, logger, callback=None):
        self.settings = settings
        self.logger = logger
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 200  # Lower for better sensitivity
        self.recognizer.dynamic_energy_threshold = False  # Fixed threshold
        self.recognizer.pause_threshold = 0.8  # Shorter pause to stop listening
        try:
            self.microphone = sr.Microphone()
            print("Voice: Microphone initialized successfully")
        except Exception as e:
            print(f"Voice: Microphone init failed: {e}")
            self.microphone = None
        self.running = False
        self.thread = None
        self.callback = callback

    def start_listening(self):
        if self.running or self.microphone is None:
            print("Voice: Not starting - running:", self.running, "mic:", self.microphone is not None)
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("Voice: Thread started")

    def stop_listening(self):
        self.running = False

    def _listen_loop(self):
        print("Voice: Listen loop started")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Voice: Adjusted for noise")
            while self.running:
                try:
                    print("Voice: Listening for audio...")
                    audio = self.recognizer.listen(source, phrase_time_limit=5)
                    print("Voice: Got audio, recognizing...")
                    text = self.recognizer.recognize_google(audio)
                    print("Voice: Recognized:", text)
                    self.logger.log_voice({"text": text})
                    if self.callback:
                        self.callback(text)
                except sr.UnknownValueError:
                    print("Voice: Unknown value, continuing")
                    continue
                except Exception as e:
                    print("Voice: Exception:", e)
                    continue

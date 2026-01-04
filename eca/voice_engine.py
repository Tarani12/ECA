import threading
import speech_recognition as sr

class VoiceEngine:
    def __init__(self, settings, logger, callback=None):
        self.callback = callback
        self.logger = logger

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

        try:
            # 🔥 FORCE MIC INDEX = 1
            self.microphone = sr.Microphone(device_index=1)
            print("VOICE: Microphone ready (index 1)")
        except Exception as e:
            print("VOICE: Microphone error:", e)
            self.microphone = None

        self.running = False

    def start_listening(self):
        if self.running or not self.microphone:
            print("VOICE: Cannot start")
            return

        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        print("VOICE: Started listening")

    def stop_listening(self):
        self.running = False
        print("VOICE: Stopped")

    def _listen_loop(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

            while self.running:
                try:
                    print("VOICE: Speak...")
                    audio = self.recognizer.listen(source)
                    text = self.recognizer.recognize_google(audio)
                    print("VOICE HEARD:", text)

                    if self.callback:
                        self.callback(text)

                except sr.UnknownValueError:
                    print("VOICE: Could not understand")
                except Exception as e:
                    print("VOICE ERROR:", e)
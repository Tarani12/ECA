import json, time, os
class Logger:
    def __init__(self, path=None):
        self.path = path or os.path.join(os.getcwd(), "eca_logs.json")
        self._data = {"gaze": [], "keys": [], "voice": [], "calibration": []}
        self._save()
    def _save(self):
        try:
            with open(self.path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass
    def log_gaze(self, g):
        self._data["gaze"].append({"ts": time.time(), **g})
        self._save()
    def log_key(self, k):
        self._data["keys"].append({"ts": time.time(), **k})
        self._save()
    def log_voice(self, v):
        self._data["voice"].append({"ts": time.time(), **v})
        self._save()
    def log_calibration(self, c):
        self._data["calibration"].append({"ts": time.time(), **c})
        self._save()

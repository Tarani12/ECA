import json
import os

DEFAULTS = {
    "dwell": 900,
    "smoothing": 0.25,
    "theme": "dark",
    "confidence": 0.35
}

class Settings:
    def __init__(self, path=None):
        self.path = path or os.path.join(os.getcwd(), "settings.json")
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = DEFAULTS.copy()
        else:
            self._data = DEFAULTS.copy()
            self.save()
    def get(self, key):
        return self._data.get(key, DEFAULTS.get(key))
    def set(self, key, value):
        self._data[key] = value
        self.save()
    def save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

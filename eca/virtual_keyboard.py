import tkinter as tk
import time
import threading

# Full US-style keyboard layout (compact, coding-friendly)
KEY_LAYOUT = [
    # Numbers + symbols
    ["1","2","3","4","5","6","7","8","9","0",
     "%","^","&","*","(",")","`"],

    # QWERTY row
    ["q","w","e","r","t","y","u","i","o","p",
     "[","]","\\","+","BACKSPACE"],

    # Home row
    ["CAPSLOCK",
     "a","s","d","f","g","h","j","k","l",
     ";","'",":","\"","ENTER"],

    # Bottom row
    ["z","x","c","v","b","n","m",
     ",",".","<",">","/","?","$","#"],

    # Coding / operators
    ["(",")","{","}","_","|","~","TAB","SPACE","DEL"],

    # Additional symbols
    ["!", "@", "#", "$", "%", "^", "&", "*", "-", "+", "=", "[", "]", "{", "}", "|", "\\"],

    # More symbols
    ["`", "~", ";", ":", "'", "\"", ",", ".", "<", ">", "/", "?"]
]



class VirtualKeyboard(tk.Frame):
    def __init__(self, parent, settings, on_key, dwell_ms=None):
        super().__init__(parent)
        self.settings = settings
        self.on_key = on_key
        self.dwell = int(dwell_ms if dwell_ms is not None else int(self.settings.get("dwell") or 900))
        self.buttons = []
        self.hover = None
        self.progress = 0.0
        self._running = True
        self._create_keys()
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _create_keys(self):
        for r, row in enumerate(KEY_LAYOUT):
            fr = tk.Frame(self)
            fr.pack(anchor="center")
            for k in row:
                width = 8
                if k == "SPACE":
                    width = 12
                if k in ("ENTER", "BACKSPACE", "TAB", "RUN"):
                    width = 10

                b = tk.Label(
                    fr,
                    text=k,
                    bd=2,
                    relief="raised",
                    width=width,
                    height=2,
                    font=("Consolas", 14),
                    bg="white"
                )
                b.pack(side="left", padx=4, pady=4)
                self.buttons.append({"widget": b, "key": k, "x": 0, "y": 0, "w": 0, "h": 0})

        self.update_idletasks()
        self._measure_buttons()

    def _measure_buttons(self):
        for item in self.buttons:
            w = item["widget"]
            try:
                item.update({
                    "x": w.winfo_rootx(),
                    "y": w.winfo_rooty(),
                    "w": w.winfo_width(),
                    "h": w.winfo_height()
                })
            except Exception:
                pass

    def set_hover_by_coords(self, sx, sy):
        hit = None
        for item in self.buttons:
            x, y, w, h = item["x"], item["y"], item["w"], item["h"]
            if x <= sx <= x + w and y <= sy <= y + h:
                hit = item
                break

        if hit is not self.hover:
            if self.hover:
                try:
                    self.hover["widget"].config(relief="raised")
                except Exception:
                    pass

            self.hover = hit
            self.progress = 0.0

            if self.hover:
                try:
                    self.hover["widget"].config(relief="sunken")
                except Exception:
                    pass

    def _update_loop(self):
        while self._running:
            if self.hover:
                step = 50
                self.progress += step / max(1, self.dwell)
                if self.progress >= 1.0:
                    key = self.hover["key"]
                    try:
                        self.on_key(key)
                    except Exception:
                        pass
                    self.progress = 0.0
            else:
                self.progress = 0.0
            time.sleep(0.05)

    def stop(self):
        self._running = False
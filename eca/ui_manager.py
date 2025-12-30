import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
import subprocess, sys, os

import cv2
from PIL import Image, ImageTk

from .ai.code_suggester import CodeSuggester
from .ai.error_checker import ErrorChecker
from .virtual_keyboard import VirtualKeyboard
from .calibration import Calibration


class UIManager:
    def __init__(self, settings, gaze, voice, command_engine, logger):
        self.settings = settings
        self.gaze = gaze
        self.voice = voice
        self.command_engine = command_engine
        self.logger = logger

        self.code_suggester = CodeSuggester()
        self.error_checker = ErrorChecker()

        # 🔥 FORCE VOICE STATE RESET
        self.voice.running = False
        self.voice.callback = self._on_voice_text

        self.root = tk.Tk()
        self.root.title("ECA - Eye & Voice Coding Assistant")

        self._build_ui()
        self._running = False

    # ================= UI =================
    def _build_ui(self):
        # ---------- NAVBAR ----------
        top = tk.Frame(self.root)
        top.pack(side="top", fill="x")

        self.language = tk.StringVar(value="Python")
        tk.OptionMenu(
            top, self.language,
            "Python", "C", "C++", "Java", "JavaScript", "C#"
        ).pack(side="left", padx=4)

        self.voice_button = tk.Button(
            top, text="Start Voice",
            command=self._toggle_voice
        )
        self.voice_button.pack(side="left", padx=2)

        tk.Button(top, text="Calibration",
                  command=self._start_calibration).pack(side="left", padx=2)

        tk.Button(top, text="Run Code",
                  command=self._run_code).pack(side="left", padx=2)

        # ---------- MAIN ----------
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)

        self.editor = ScrolledText(
            main, font=("Consolas", 14), undo=True
        )
        self.editor.pack(fill="both", expand=True, padx=8, pady=6)
        self.editor.bind("<KeyRelease>", self._on_key_release)

        # ---------- CAMERA ----------
        self.cam_preview = tk.Label(self.root, bd=2, relief="solid")
        self.cam_preview.place(relx=0.99, y=8, anchor="ne")

        # ---------- AI PANEL ----------
        self.ai_panel = tk.Frame(
            self.root, width=240,
            bg="#1e1e1e", bd=2, relief="solid"
        )
        self.ai_panel.place(relx=0.99, y=180, anchor="ne")

        tk.Label(
            self.ai_panel, text="AI Suggestions",
            fg="white", bg="#1e1e1e",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(6, 2))

        self.suggestion_box = tk.Listbox(
            self.ai_panel, height=6,
            bg="#252526", fg="white"
        )
        self.suggestion_box.pack(fill="x", padx=6)

        tk.Button(
            self.ai_panel, text="Insert",
            command=self._apply_suggestion
        ).pack(pady=6)

        tk.Label(
            self.ai_panel, text="Detected Issues",
            fg="white", bg="#1e1e1e",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(6, 2))

        self.error_box = tk.Listbox(
            self.ai_panel, height=5,
            bg="#252526", fg="#ff6b6b"
        )
        self.error_box.pack(fill="x", padx=6, pady=(0, 6))

        # ---------- KEYBOARD ----------
        self.keyboard = VirtualKeyboard(
            self.root, self.settings, self._on_key
        )
        self.keyboard.place(relx=0.5, rely=0.9, anchor="center")

        self.kb_dot = tk.Canvas(
            self.root, width=12, height=12, highlightthickness=0
        )
        self.kb_dot.create_oval(2, 2, 10, 10, fill="red")

        # ---------- STATUS ----------
        self.status = tk.Label(
            self.root, text="Ready",
            anchor="e", font=("Segoe UI", 8)
        )
        self.status.place(relx=1.0, rely=1.0, anchor="se")

    # ================= START =================
    def start(self):
        self._running = True
        self.gaze.start()
        self._loop()
        self.root.mainloop()

    # ================= LOOP =================
    def _loop(self):
        with self.gaze.lock:
            gx, gy = self.gaze.gx, self.gaze.gy
            conf, fps = self.gaze.conf, self.gaze.fps
            frame = self.gaze.frame

        try:
            self.keyboard._measure_buttons()
            kx, ky = self.keyboard.winfo_rootx(), self.keyboard.winfo_rooty()
            kw, kh = self.keyboard.winfo_width(), self.keyboard.winfo_height()

            sx = int(kx + gx * kw)
            sy = int(ky + gy * kh)

            if sy < ky - 40:
                self.keyboard.hover = None
                self.keyboard.progress = 0
                self.kb_dot.place_forget()
            else:
                self.keyboard.set_hover_by_coords(sx, sy)
                rx = sx - self.root.winfo_rootx()
                ry = sy - self.root.winfo_rooty()
                self.kb_dot.place(x=rx - 6, y=ry - 6)
        except Exception:
            pass

        try:
            if frame is not None:
                frame = cv2.resize(frame, (200, 150))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(Image.fromarray(frame))
                self.cam_preview.configure(image=img)
                self.cam_preview.image = img
        except Exception:
            pass

        self.status.config(text=f"Conf: {conf:.2f} | FPS: {fps:.1f}")
        self.root.after(40, self._loop)

    # ================= AI =================
    def _on_key_release(self, _):
        self._update_suggestions()
        self._highlight_errors()

    def _update_suggestions(self):
        self.suggestion_box.delete(0, tk.END)
        for s in self.code_suggester.suggest(self.editor.get("1.0", "end")):
            self.suggestion_box.insert(tk.END, s)

    def _highlight_errors(self):
        self.editor.tag_remove("error", "1.0", tk.END)
        self.error_box.delete(0, tk.END)
        for err in self.error_checker.check_errors(self.editor.get("1.0", "end")):
            self.error_box.insert(tk.END, f"Line {err['line']}: {err['hint']}")
            self.editor.tag_add("error", f"{err['line']}.0", f"{err['line']}.end")
        self.editor.tag_config("error", foreground="red", underline=True)

    def _apply_suggestion(self):
        if not self.suggestion_box.curselection():
            return

        suggestion = self.suggestion_box.get(
            self.suggestion_box.curselection()
        )
    # --- REMOVE LAST TYPED WORD ---
        cursor = self.editor.index("insert")
        line_start = self.editor.index("insert linestart")
        text_before = self.editor.get(line_start, cursor)

    # Split to words
        parts = text_before.rstrip().split()

        if parts:
            last_word = parts[-1]
        # delete only the last word
            self.editor.delete(f"{cursor}-{len(last_word)}c", cursor)

    # --- INSERT FULL TEMPLATE ---
        self.editor.insert("insert", suggestion)

    # --- AUTO INDENT ---
        if suggestion.strip().endswith(":"):
            self.editor.insert("insert", "\n    ")

    # Refresh AI
        self._update_suggestions()
        self._highlight_errors()

    # ================= INPUT =================
    def _on_key(self, key):
        if key == "SPACE":
            self.editor.insert("insert", " ")
        elif key == "ENTER":
            self.editor.insert("insert", "\n")
        elif key == "BACKSPACE":
            self.editor.delete("insert-1c")
        else:
            self.editor.insert("insert", key)
        self._update_suggestions()
        self._highlight_errors()

    # ================= VOICE =================
    def _toggle_voice(self):
        print("[VOICE] Toggle")

        if self.voice.running:
            print("[VOICE] Stopping")
            self.voice.running = False
            self.voice.stop_listening()
            self.voice_button.config(text="Start Voice")
        else:
            print("[VOICE] Starting")
            self.voice.running = True
            self.voice.callback = self._on_voice_text
            self.voice.start_listening()
            self.voice_button.config(text="Stop Voice")

    def _on_voice_text(self, text):
        print("[VOICE TEXT]:", text)

        if not text:
            return

        t = text.lower().strip()

        if "for loop" in t or "create a loop" in t:
            self.editor.insert("insert", "for i in range():\n    ")
        elif "while loop" in t:
            self.editor.insert("insert", "while condition:\n    ")
        elif t.startswith("if"):
            self.editor.insert("insert", "if condition:\n    ")
        elif "elif" in t:
            self.editor.insert("insert", "elif condition:\n    ")
        elif t.startswith("else"):
            self.editor.insert("insert", "else:\n    ")
        elif "function" in t:
            self.editor.insert("insert", "def function_name():\n    ")
        elif "class" in t:
            self.editor.insert("insert", "class ClassName:\n    def __init__(self):\n        ")
        elif "print" in t:
            self.editor.insert("insert", 'print("")')
        elif "import" in t:
            self.editor.insert("insert", "import module_name")
        else:
            self.editor.insert("insert", text + " ")

        self._update_suggestions()
        self._highlight_errors()

    # ================= RUN CODE =================
    def _run_code(self):
        if self.language.get() != "Python":
            messagebox.showinfo("Compiler", "Compiler available only for Python")
            return

        code = self.editor.get("1.0", "end-1c").strip()
        if not code:
            return

        tmp = os.path.join(os.getcwd(), "eca_temp_run.py")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            out = subprocess.check_output(
                [sys.executable, tmp],
                stderr=subprocess.STDOUT,
                timeout=10,
                text=True
            )
            messagebox.showinfo("Output", out)
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("Error", e.output)

    def _start_calibration(self):
        pass
class CommandEngine:
    def __init__(self, logger):
        self.logger = logger
        self.typing_enabled = True

    def interpret(self, text):
        t = text.lower().strip()

        # -------- NORMALIZE SPEECH ERRORS --------
        t = t.replace("inert", "insert")
        t = t.replace("inside", "insert")
        t = t.replace("intend", "indent")

        # -------- PAUSE / RESUME (ALWAYS ALLOWED) --------
        if t in ("pause typing", "stop typing"):
            self.typing_enabled = False
            return ("pause", "Typing paused")

        if t in ("resume typing", "start typing"):
            self.typing_enabled = True
            return ("resume", "Typing resumed")

        # -------- BLOCK EVERYTHING ELSE WHEN PAUSED --------
        if not self.typing_enabled:
            return ("blocked", None)

        # -------- NAVIGATION / EDITING --------
        if t in ("new line", "next line"):
            return ("insert", "\n")

        if t == "indent":
            return ("insert", "    ")

        if t == "dedent":
            return ("dedent", None)

        if t == "backspace":
            return ("backspace", None)

        if t == "delete line":
            return ("delete_line", None)

        if t == "clear line":
            return ("clear_line", None)

        # -------- SYMBOLS --------
        symbols = {
            "open bracket": "{",
            "close bracket": "}",
            "open parenthesis": "(",
            "close parenthesis": ")",
            "open square bracket": "[",
            "close square bracket": "]",
            "colon": ":",
            "comma": ",",
            "dot": ".",
            "equals": "=",
            "plus": "+",
            "minus": "-",
            "multiply": "*",
            "divide": "/"
        }

        if t in symbols:
            return ("insert", symbols[t])

        # -------- CODE SNIPPETS --------
        if t == "insert for loop":
            return ("insert", "for i in range():\n    ")

        if t == "insert while loop":
            return ("insert", "while condition:\n    ")

        if t == "insert if condition":
            return ("insert", "if condition:\n    ")

        if t == "insert else":
            return ("insert", "else:\n    ")

        if t == "insert function":
            return ("insert", "def function_name():\n    ")

        if t == "insert class":
            return ("insert", "class ClassName:\n    def __init__(self):\n        ")

        if t == "insert print":
            return ("insert", "print()")

        if t == "insert main":
            return ("insert", "if __name__ == '__main__':\n    ")

        # -------- FALLBACK (DICTATION) --------
        return ("dictation", text)
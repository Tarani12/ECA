import re

class CommandEngine:
    def __init__(self, logger):
        self.logger = logger

    def interpret(self, text):
        t = text.lower().strip()
        if t == "new line":
            return ("insert", "\n")
        if t == "space":
            return ("insert", " ")
        if t == "indent":
            return ("insert", "    ")
        if t == "backspace":
            return ("backspace", None)
        if t == "delete line":
            return ("delete_line", None)
        if t == "run code":
            return ("run", None)
        m = re.match(r"type (.+)", t)
        if m:
            return ("insert", m.group(1))
        m = re.match(r"define function (.+)", t)
        if m:
            name = m.group(1).strip()
            return ("insert", f"def {name}():\n    pass\n")
        return ("insert", text)

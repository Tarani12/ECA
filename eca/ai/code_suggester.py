# eca/ai/code_suggester.py

import re

TEMPLATES = {
    "for": [
        "for i in range():",
        "for i in range(1, 10):",
        "for i in range(len()):"
    ],
    "if": [
        "if condition:",
        "if x > y:"
    ],
    "while": [
        "while condition:"
    ],
    "def": [
        "def function_name():"
    ],
    "print": [
        'print("")'
    ]
}

class CodeSuggester:
    def __init__(self, max_suggestions=5):
        self.max_suggestions = max_suggestions

    def _get_token(self, text):
        lines = text.rstrip().split("\n")
        if not lines:
            return ""

        last_line = lines[-1].strip().lower()

        # 🔥 VERY IMPORTANT FALLBACK LOGIC
        if last_line.startswith("for"):
            return "for"
        if last_line.startswith("if"):
            return "if"
        if last_line.startswith("while"):
            return "while"
        if last_line.startswith("def"):
            return "def"
        if last_line.startswith("print"):
            return "print"

        # normal word detection
        words = re.findall(r"[a-zA-Z_]+", last_line)
        return words[-1] if words else ""

    def suggest(self, editor_text):
        token = self._get_token(editor_text)

        if token in TEMPLATES:
            return TEMPLATES[token][:self.max_suggestions]

        return []
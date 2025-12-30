# eca/ai/error_checker.py

import ast
import difflib

COMMON_MISTAKES = {
    "rnage": "range",
    "pritn": "print",
    "fucntion": "function",
}

class ErrorChecker:
    """
    AI-assisted error detection with fix hints.
    """

    def check_errors(self, code_text):
        errors = []

        # 1️⃣ Syntax errors (AST based)
        try:
            ast.parse(code_text)
        except SyntaxError as e:
            errors.append({
                "line": e.lineno,
                "message": e.msg,
                "hint": "Check syntax near this line"
            })

        # 2️⃣ Common typo detection
        lines = code_text.split("\n")
        for idx, line in enumerate(lines):
            words = line.split()
            for w in words:
                if w in COMMON_MISTAKES:
                    errors.append({
                        "line": idx + 1,
                        "message": f"Possible typo: '{w}'",
                        "hint": f"Did you mean '{COMMON_MISTAKES[w]}'?"
                    })

                # fuzzy match for keywords
                matches = difflib.get_close_matches(
                    w, COMMON_MISTAKES.values(), n=1, cutoff=0.85
                )
                if matches and w not in COMMON_MISTAKES.values():
                    errors.append({
                        "line": idx + 1,
                        "message": f"Suspicious word: '{w}'",
                        "hint": f"Did you mean '{matches[0]}'?"
                    })

        return errors
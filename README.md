# ECA - Iris Real-Time Working Fix

This package improves camera startup and MediaPipe initialization timing for more reliable iris detection.

## Key fixes
- MediaPipe FaceMesh is initialized when camera starts.
- VideoCapture uses DirectShow on Windows and sets resolution hints.
- FPS and confidence updates are computed reliably.
- Gaze dot moves based on calibrated mapping.

## Voice Commands
The application supports voice commands for code insertion. Click "Start Voice" to begin listening. Say one of the following to insert code snippets, or speak any text to insert it directly:

- "for loop" or "loop" → inserts `for i in range():\n    `
- "while loop" → inserts `while condition:\n    `
- "if" → inserts `if condition:\n    `
- "else" → inserts `else:\n    `
- "elif" or "else if" → inserts `elif condition:\n    `
- "print" → inserts `print("")`
- "function" or "def" → inserts `def function_name():\n    `
- "class" → inserts `class ClassName:\n    def __init__(self):\n        `
- "try" → inserts `try:\n    \nexcept Exception as e:\n    `
- "import" → inserts `import module_name`

Any other spoken text will be inserted directly into the editor.

## Troubleshooting Voice
If voice is not working:
- Ensure your microphone is enabled and set as default in Windows settings.
- Speak clearly and close to the microphone.
- The button will change to "Stop Voice" when listening.
- If recognition fails, it may be due to background noise; try in a quiet environment.
- Requires internet for Google recognition; offline fallback is available but may be less accurate.

## Run
Install requirements:
pip install opencv-python mediapipe SpeechRecognition PyAudio
python run_app.py

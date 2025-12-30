import threading, time, math, os
import cv2
import numpy as np

# Try to import MediaPipe; if not available, user must pip install mediapipe
try:
    import mediapipe as mp
    MP_AVAILABLE = True
except Exception:
    mp = None
    MP_AVAILABLE = False

class GazeTracker:
    """
    Iris-based gaze tracker using MediaPipe FaceMesh refined landmarks.
    FaceMesh instance is created when camera starts to avoid initialization issues.
    """
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger
        self.cap = None
        self.running = False
        self.frame = None
        self.annotated = None
        self.gx = 0.5
        self.gy = 0.5
        self.conf = 0.0
        self.fps = 0.0
        self.lock = threading.Lock()
        self.smoothing = float(self.settings.get("smoothing") or 0.25)
        self.thread = None
        self._mp_face = None

    def start(self, cam_index=0):
        if self.running:
            return
        # initialize camera capture robustly
        self.cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW if os.name == 'nt' else cam_index)
        # set capture properties (helpful on Windows)
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
        except Exception:
            pass

        # initialize MediaPipe FaceMesh once
        if MP_AVAILABLE and self._mp_face is None:
            try:
                mp_face_mesh = mp.solutions.face_mesh
                self._mp_face = mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                print("MediaPipe FaceMesh initialized")
            except Exception as e:
                print("MediaPipe init failed:", e)
                self._mp_face = None

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        # do not close self._mp_face here; keep for reuse

    def _annotate(self, frame, lm_coords, left_center=None, right_center=None):
        img = frame.copy()
        h,w = img.shape[:2]
        # draw landmarks provided (limit to avoid heavy drawing)
        for (x,y) in lm_coords[:100]:
            cv2.circle(img, (int(x*w), int(y*h)), 1, (0,255,0), -1)
        if left_center:
            cv2.circle(img, (int(left_center[0]*w), int(left_center[1]*h)), 3, (0,0,255), -1)
        if right_center:
            cv2.circle(img, (int(right_center[0]*w), int(right_center[1]*h)), 3, (255,0,0), -1)
        return img

    def _run(self):
        prev_time = time.time()
        frame_count = 0
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            frame_count += 1
            now = time.time()
            h, w = frame.shape[:2]
            gx = 0.5; gy = 0.5; conf = 0.0
            left_center = None; right_center = None
            lm_coords = []

            if MP_AVAILABLE and self._mp_face:
                try:
                    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self._mp_face.process(img_rgb)
                    if results.multi_face_landmarks:
                        # debug print for detection (prints infrequently)
                        # print("✔️ Face detected")
                        face_lms = results.multi_face_landmarks[0]
                        # collect some landmarks for annotation
                        for lm in face_lms.landmark:
                            lm_coords.append((lm.x, lm.y))
                        # iris landmark indices (MediaPipe)
                        left_idx = [468,469,470,471]
                        right_idx = [473,474,475,476]
                        try:
                            lpts = [(face_lms.landmark[i].x, face_lms.landmark[i].y) for i in left_idx]
                            rpts = [(face_lms.landmark[i].x, face_lms.landmark[i].y) for i in right_idx]
                            lx = sum([p[0] for p in lpts]) / len(lpts)
                            ly = sum([p[1] for p in lpts]) / len(lpts)
                            rx = sum([p[0] for p in rpts]) / len(rpts)
                            ry = sum([p[1] for p in rpts]) / len(rpts)
                            left_center = (lx, ly)
                            right_center = (rx, ry)
                            gx = (lx + rx) / 2.0
                            gy = (ly + ry) / 2.0
                            gx = 1 - gx  # Flip horizontal for correct direction
                            conf = 0.9
                        except Exception:
                            gx = 0.5; gy = 0.5; conf = 0.0
                    else:
                        # no face landmarks
                        # print("❌ No face detected")
                        gx = 0.5; gy = 0.5; conf = 0.0
                except Exception as e:
                    # if MediaPipe processing fails, fallback
                    print("MediaPipe processing exception:", e)
                    gx = 0.5; gy = 0.5; conf = 0.0
            else:
                # fallback: coarse face detection using Haar cascade to get face center
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    if len(faces)>0:
                        x,y,wf,hf = faces[0]
                        gx = (x + wf/2.0) / w
                        gy = (y + hf/2.0) / h
                        gx = 1 - gx  # Flip horizontal for correct direction
                        conf = 0.4
                    else:
                        gx = 0.5; gy = 0.5; conf = 0.0
                except Exception:
                    gx = 0.5; gy = 0.5; conf = 0.0

            # smoothing (EWMA)
            with self.lock:
                alpha = float(self.smoothing)
                self.gx = alpha * gx + (1-alpha) * self.gx
                self.gy = alpha * gy + (1-alpha) * self.gy
                self.conf = float(conf)
                self.frame = frame
                self.annotated = self._annotate(frame, lm_coords, left_center, right_center)
                frame_count_local = frame_count
                elapsed = now - prev_time
                self.fps = frame_count_local / max(0.001, elapsed)

            self.logger.log_gaze({"gx": float(self.gx), "gy": float(self.gy), "conf": float(self.conf), "fps": float(self.fps)})
            time.sleep(0.01)

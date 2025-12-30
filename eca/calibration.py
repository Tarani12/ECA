import json, time, os
import threading

class Calibration:
    def __init__(self, gaze_tracker, logger, samples_per_point=25):
        self.gaze = gaze_tracker
        self.logger = logger
        self.samples = samples_per_point
        self.mapping = None

    def run_9_point(self, get_screen_point, show_target_at, collect_sleep=0.02):
        samples = []
        for idx in range(9):
            sx, sy = get_screen_point(idx)
            show_target_at(sx, sy)
            buf = []
            cnt = 0
            while cnt < self.samples:
                with self.gaze.lock:
                    gx = self.gaze.gx
                    gy = self.gaze.gy
                buf.append((gx, gy))
                cnt += 1
                time.sleep(collect_sleep)
            avgx = sum([b[0] for b in buf]) / len(buf)
            avgy = sum([b[1] for b in buf]) / len(buf)
            samples.append({"screen": (sx, sy), "gaze": (avgx, avgy)})
        import numpy as np
        A = []
        Bx = []
        By = []
        for s in samples:
            gx, gy = s["gaze"]
            sx, sy = s["screen"]
            A.append([gx, gy, 1])
            Bx.append(sx)
            By.append(sy)
        A = np.array(A)
        Bx = np.array(Bx)
        By = np.array(By)
        try:
            px, _, _, _ = np.linalg.lstsq(A, Bx, rcond=None)
            py, _, _, _ = np.linalg.lstsq(A, By, rcond=None)
            self.mapping = {"px": px.tolist(), "py": py.tolist()}
            path = os.path.join(os.getcwd(), "calibration_map.json")
            with open(path, "w") as f:
                json.dump(self.mapping, f, indent=2)
            self.logger.log_calibration({"mapping": self.mapping})
            return True
        except Exception:
            return False

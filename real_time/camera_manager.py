# real_time/camera_manager.py
import cv2
import platform
import time


class CameraManager:
    """Handles camera initialization, frame capture and cleanup"""

    def __init__(self, camera_index=0, frame_width=640, frame_height=360, target_fps=30):
        self.camera_index = camera_index
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.target_fps = target_fps
        self.cap = None
        self.is_running = False
        self.last_error = ""

    def _try_open_once(self, index, backend=None):
        """Try to open a capture with the given index/backend."""
        try:
            cap = cv2.VideoCapture(index, backend) if backend is not None else cv2.VideoCapture(index)
        except Exception:
            cap = cv2.VideoCapture(index)
        if cap is not None and cap.isOpened():
            self.cap = cap
            return True
        return False

    def _open_capture(self) -> bool:
        """Try several indices (0..3) and both backends; store reason if all fail."""
        self.last_error = ""
        self.cap = None

        indices = [self.camera_index, 0, 1, 2, 3]
        seen = set()
        indices = [i for i in indices if not (i in seen or seen.add(i))]  # dedupe

        backends = []
        if platform.system() == "Darwin":
            backends.append(cv2.CAP_AVFOUNDATION)  # best on macOS
        backends.append(None)  # default backend

        # Tiny retry (helps when another app just released the camera)
        for idx in indices:
            for be in backends:
                for _ in range(2):
                    if self._try_open_once(idx, be):
                        self.camera_index = idx
                        return True
                    time.sleep(0.15)

        self.last_error = f"Could not open camera using indices {indices} with AVFoundation and default backends."
        return False

    def start(self) -> bool:
        """Initialize and configure the camera. Returns True if ready."""
        if not self._open_capture():
            self.is_running = False
            return False

        # Best-effort property set
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)

        self.is_running = True
        return True

    def read_frame(self):
        """Read and return a frame from the camera."""
        if not self.is_running or self.cap is None:
            return False, None

        t0 = time.time()
        ok, frame = self.cap.read()

        # Frame rate control
        dt = time.time() - t0
        sleep_time = (1.0 / max(self.target_fps, 1)) - dt
        if sleep_time > 0:
            time.sleep(sleep_time)

        return ok, frame

    def stop(self):
        """Release camera resources."""
        self.is_running = False
        if self.cap is not None:
            try:
                self.cap.release()
            finally:
                self.cap = None

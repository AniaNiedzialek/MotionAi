import cv2
import time

class CameraManager:
    """Handles camera initialization, frame capture and cleanup"""
    
    def __init__(self, camera_index=0, frame_width=640, frame_height=480, target_fps=30):
        self.camera_index = camera_index
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.target_fps = target_fps
        self.cap = None
        self.is_running = False

    def start(self):
        """Initialize and configure the camera"""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera {self.camera_index}")
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        self.is_running = True
        return True

    def read_frame(self):
        """Read and return a frame from the camera"""
        if not self.is_running or self.cap is None:
            return False, None
            
        loop_start = time.time()
        success, frame = self.cap.read()
        
        # Frame rate control
        elapsed = time.time() - loop_start
        sleep_time = (1.0 / self.target_fps) - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
            
        return success, frame

    def stop(self):
        """Release camera resources"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
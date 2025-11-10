import customtkinter as ctk
import cv2
import threading
import time
from PIL import Image, ImageTk

from camera_manager import CameraManager
from pose_processor import PoseProcessor
from motion_comparer import MotionComparer
from motion_player import MotionPlayer
from database import MotionDatabase

# Configuration
CAMERA_INDEX = 0
TARGET_FPS = 30
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
ADVANCE_SCORE_THRESHOLD = 98.0

class MotionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.db = MotionDatabase()
        self.camera_manager = CameraManager(
            camera_index=CAMERA_INDEX, 
            frame_width=FRAME_WIDTH,
            frame_height=FRAME_HEIGHT,
            target_fps=TARGET_FPS
        )
        self.pose_processor = PoseProcessor()
        self.motion_comparer = MotionComparer()
        self.motion_player = MotionPlayer(self.db)
        
        # App state
        self.is_running = False
        self.processing_thread = None
        self.last_frame = None
        self.last_score = 0.0
        self.last_feedback = "Waiting..."
        self.last_deviations = set()
        self.pro_data_loaded = False
        
        # Setup UI
        self.setup_ui()
        
        # Start UI update loop
        self.update_ui_elements()
        
        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Initialize and configure all UI components"""
        self.title("Real-time Motion Instructor")
        self.geometry("800x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Video row
        
        # --- Top Control Frame ---
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.control_frame.grid_columnconfigure(2, weight=1)
        
        self.start_stop_button = ctk.CTkButton(
            self.control_frame, 
            text="Start Practice", 
            command=self.toggle_session
        )
        self.start_stop_button.grid(row=0, column=0, padx=5)
        
        self.load_pro_button = ctk.CTkButton(
            self.control_frame, 
            text="Load Motion", 
            command=self.load_pro_data_action
        )
        self.load_pro_button.grid(row=0, column=1, padx=5)
        
        self.add_motion_button = ctk.CTkButton(
            self.control_frame, 
            text="Add New Motion", 
            command=self.add_new_motion
        )
        self.add_motion_button.grid(row=0, column=2, padx=5)
        
        self.status_label = ctk.CTkLabel(
            self.control_frame, 
            text="Status: Idle. Load motion first.", 
            anchor="w"
        )
        self.status_label.grid(row=0, column=3, padx=10, sticky="ew")
        self.control_frame.grid_columnconfigure(3, weight=1)
        
        # --- Video Display ---
        self.video_label = ctk.CTkLabel(self, text="Camera Feed", fg_color="gray20")
        self.video_label.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # --- Feedback Frame ---
        self.feedback_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.feedback_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.feedback_frame.grid_columnconfigure(0, weight=1)
        
        self.score_label = ctk.CTkLabel(
            self.feedback_frame, 
            text="Score: --", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.score_label.grid(row=0, column=0, padx=5, sticky="w")
        
        self.feedback_text_label = ctk.CTkLabel(
            self.feedback_frame, 
            text="Feedback: Waiting...", 
            anchor="w", 
            justify="left"
        )
        self.feedback_text_label.grid(row=1, column=0, padx=5, sticky="ew")
        
    def load_pro_data_action(self):
        """Load motion data from database using selection dialog"""
        # Open motion selection dialog
        from motion_manager import MotionSelectionDialog
        dialog = MotionSelectionDialog(self)
        self.wait_window(dialog)
        
        # Check if a motion was selected
        if dialog.selected_motion_id:
            motion_id = dialog.selected_motion_id
            
            if self.motion_player.load_motion(motion_id):
                # Find motion name
                motions = self.db.get_motions_list()
                motion_name = next((m["name"] for m in motions if m["id"] == motion_id), "Unknown")
                
                frame_count = self.motion_player.get_frame_count()
                self.status_label.configure(text=f"Status: Loaded '{motion_name}' ({frame_count} frames). Ready.")
                self.pro_data_loaded = True
            else:
                self.status_label.configure(text="Status: Error loading motion data.")
                self.pro_data_loaded = False
                
    def toggle_session(self):
        """Start or stop the practice session"""
        if not self.pro_data_loaded or self.motion_player.get_frame_count() == 0:
            self.status_label.configure(text="Status: Please load valid professional data first!")
            return
            
        if self.is_running:  # If running, stop it
            self.is_running = False
            self.start_stop_button.configure(text="Start Practice")
            self.load_pro_button.configure(state="normal")
            self.status_label.configure(text="Status: Stopping...")
            self.after(100, self.check_thread_join)
            
        else:  # If not running, start continuous playback
            self.is_running = True
            self.start_stop_button.configure(text="Stop Practice")
            self.load_pro_button.configure(state="disabled")
            self.status_label.configure(text="Status: Session Running")
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self.process_frames_loop, 
                daemon=True
            )
            self.processing_thread.start()
            
    def check_thread_join(self):
        """Check if processing thread has finished"""
        if self.processing_thread is not None and self.processing_thread.is_alive():
            print("Waiting for processing thread to finish...")
            self.after(100, self.check_thread_join)
        else:
            print("Processing thread has finished.")
            self.processing_thread = None
            self.status_label.configure(text="Status: Idle.")
            
    
    def process_frames_loop(self):
        """Main processing loop running in a separate thread."""
        PROCESS_EVERY = 3            # run mediapipe every N frames for perf
        MISS_TOLERANCE = 10          # frames allowed without a new detection (~1/3 sec)
        print("DEBUG: process_frames thread started")

        try:
            if not self.camera_manager.start():
                reason = self.camera_manager.last_error or "Camera unavailable"
                print(f"DEBUG: camera start failed -> {reason}")
                self.last_feedback = f"Error: {reason}"
                self.is_running = False
                self.after(50, self.update_ui_elements)
                return

            print(f"DEBUG: camera opened on index {self.camera_manager.camera_index}")
            self.after(0, self.update_ui_elements)  # ensure UI loop is alive

            ticks = 0
            consecutive_fail = 0

            # ---- NEW: cache the last successful user pose/results ----
            last_user_kpts = None
            last_results = None
            miss_count = 0

            while self.is_running:
                ok, frame = self.camera_manager.read_frame()
                if not ok or frame is None:
                    consecutive_fail += 1
                    if consecutive_fail % 10 == 0:
                        print(f"DEBUG: read_frame failed x{consecutive_fail}")
                    if consecutive_fail >= 60:  # ~2 sec at 30 fps
                        print("DEBUG: too many read failures, stopping loop")
                        break
                    continue
                consecutive_fail = 0

                # -------- Pose extraction (throttled) --------
                fresh_detection = False
                try:
                    if ticks % PROCESS_EVERY == 0:
                        user_keypoints, results = self.pose_processor.extract_keypoints(frame)
                        if user_keypoints:
                            last_user_kpts = user_keypoints
                            last_results = results
                            miss_count = 0
                            fresh_detection = True
                        else:
                            miss_count += 1
                    else:
                        # reuse last pose on skipped frames
                        user_keypoints, results = last_user_kpts, last_results
                        if user_keypoints is None:
                            miss_count += 1
                except Exception as e:
                    print(f"DEBUG: extract_keypoints error: {e}")
                    import traceback; traceback.print_exc()
                    user_keypoints, results = last_user_kpts, last_results
                    miss_count += 1

                # -------- Draw user pose (reuse cached results if needed) --------
                if results is not None and getattr(results, "pose_landmarks", None):
                    try:
                        self.pose_processor.draw_pose(frame, results)
                    except Exception:
                        pass

                # Only show the “no pose” message after short streak of misses
                if miss_count > MISS_TOLERANCE:
                    self.last_feedback = "No user pose detected"

                # -------- Pro frame --------
                try:
                    pro_keypoints = self.motion_player.get_current_frame_keypoints()
                except Exception as e:
                    print(f"DEBUG: get_current_frame_keypoints error: {e}")
                    pro_keypoints = None

                # -------- Compare (only if we currently have user_keypoints) --------
                if pro_keypoints and user_keypoints:
                    try:
                        score, feedback, deviations = self.motion_comparer.calculate_similarity(
                            user_keypoints, pro_keypoints
                        )
                    except Exception as e:
                        print(f"DEBUG: similarity error: {e}")
                        score, feedback, deviations = 0.0, "Comparison error", set()

                    self.last_score = score
                    # If we just got a fresh detection, update feedback immediately;
                    # otherwise keep previous feedback to avoid flicker.
                    if fresh_detection or not self.last_feedback or self.last_feedback.startswith("No user"):
                        self.last_feedback = feedback
                    self.last_deviations = deviations

                    try:
                        self.motion_player.check_advance_frame(score)
                    except Exception as e:
                        print(f"DEBUG: check_advance_frame error: {e}")
                elif not pro_keypoints:
                    # don't spam this every frame; only when nothing to compare
                    if fresh_detection:
                        self.last_feedback = "Pro frame data missing?"
                    self.last_score = 0.0
                    self.last_deviations = set()

                # -------- Pro overlay (green) --------
                try:
                    self.pose_processor.draw_professional_pose(
                        frame, pro_keypoints, self.last_deviations, FRAME_WIDTH, FRAME_HEIGHT
                    )
                except Exception as e:
                    if ticks % 30 == 0:
                        print(f"DEBUG: draw_professional_pose error: {e}")

                # -------- UI frame --------
                try:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.last_frame = Image.fromarray(frame_rgb)
                except Exception as e:
                    if ticks % 30 == 0:
                        print(f"DEBUG: BGR2RGB error: {e}")
                    self.last_frame = None

                ticks += 1

            print("DEBUG: loop exit; is_running =", self.is_running)

        except Exception as e:
            print(f"!!! ERROR in processing thread: {e}")
            import traceback; traceback.print_exc()
            self.last_feedback = f"Error: {e}"
            self.last_frame = None
            self.last_deviations = set()
            self.is_running = False

        finally:
            self.camera_manager.stop()
            print("DEBUG: process_frames thread finished cleanup")
            self.last_frame = None
            self.last_score = 0.0
            if not str(self.last_feedback).startswith("Error:"):
                self.last_feedback = "Session stopped."
            self.after(10, self.update_ui_elements)
    
    def update_ui_elements(self):
        """Update UI with current application state (thread-safe & image-safe)."""
        from tkinter import TclError
        try:
            # ----- Video feed -----
            if self.last_frame is not None:
                try:
                    img = self.last_frame.resize((FRAME_WIDTH, FRAME_HEIGHT))
                    # Use PhotoImage and keep a strong reference
                    self._video_photo = ImageTk.PhotoImage(img)
                    self.video_label.configure(image=self._video_photo, text="")
                except TclError:
                    pass
            else:
                try:
                    self._video_photo = None
                    self.video_label.configure(image="", text="Camera Feed (Stopped)")
                except TclError:
                    pass

            # ----- Score / feedback -----
            try:
                self.score_label.configure(text=f"Score: {self.last_score:.1f}")
                self.feedback_text_label.configure(text=f"Feedback: {self.last_feedback}")
                if self.last_score >= 85:
                    self.score_label.configure(text_color="lightgreen")
                elif self.last_score >= 60:
                    self.score_label.configure(text_color="yellow")
                else:
                    self.score_label.configure(text_color="lightcoral")
            except TclError:
                pass

            # ----- Status line -----
            try:
                if self.is_running and self.pro_data_loaded:
                    frame_count = self.motion_player.get_frame_count()
                    display_index = self.motion_player.get_display_frame_number()
                    self.status_label.configure(text=f"Status: Practicing Pose {display_index}/{frame_count}")
                elif not self.is_running and self.pro_data_loaded:
                    self.status_label.configure(text=f"Status: Ready ({self.motion_player.get_frame_count()} frames).")
            except TclError:
                pass

        except Exception as e:
            import traceback
            print(f"!!! ERROR in update_ui_elements: {e}")
            traceback.print_exc()

        # Reschedule only while running (prevents late callbacks on stop)
        if self.is_running:
            self.after(33, self.update_ui_elements)

    
    def on_closing(self):
        """Handle window close event"""
        print("Closing application...")
        self.is_running = False  # Signal thread to stop
        
        # Wait briefly for thread to stop
        if self.processing_thread is not None:
            self.processing_thread.join(timeout=0.5)
            
        self.destroy()
        
    def add_new_motion(self):
        """Open dialog to add a new motion"""
        from motion_upload import MotionUploadDialog
        dialog = MotionUploadDialog(self)
        self.wait_window(dialog)
        
        # Refresh motion list if new motion was added
        motions = self.db.get_motions_list()
        if motions and (not self.pro_data_loaded):
            self.status_label.configure(text=f"Status: {len(motions)} motions available. Load one to begin.")

if __name__ == "__main__":
    app = MotionApp()
    app.mainloop()
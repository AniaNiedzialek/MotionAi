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
        """Main processing loop running in a separate thread"""
        print("DEBUG: process_frames thread started")
        
        try:
            if not self.camera_manager.start():
                self.last_feedback = "Error: Camera unavailable"
                self.is_running = False
                self.after(100, self.update_ui_elements)
                return
                
            while self.is_running:
                # Read frame from camera
                success, frame = self.camera_manager.read_frame()
                if not success:
                    print("DEBUG: cap.read() returned success=False")
                    self.last_feedback = "Error reading frame"
                    continue
                    
                # Process user pose
                user_keypoints, results = self.pose_processor.extract_keypoints(frame)
                if results.pose_landmarks:
                    self.pose_processor.draw_pose(frame, results)
                else:
                    self.last_feedback = "No user pose detected"
                    
                # Get professional pose keypoints
                pro_keypoints = self.motion_player.get_current_frame_keypoints()
                
                # Compare poses
                if pro_keypoints and user_keypoints:
                    score, feedback, deviations = self.motion_comparer.calculate_similarity(
                        user_keypoints, pro_keypoints
                    )
                    self.last_score = score
                    self.last_feedback = feedback
                    self.last_deviations = deviations
                    
                    # Check if we should advance to next pose
                    self.motion_player.check_advance_frame(score)
                elif not pro_keypoints:
                    self.last_feedback = f"Pro frame data missing?"
                    self.last_score = 0.0
                    self.last_deviations = set()
                else:
                    self.last_score = 0.0
                    self.last_deviations = set()
                    
                # Draw professional pose landmarks with highlighting
                self.pose_processor.draw_professional_pose(
                    frame, 
                    pro_keypoints, 
                    self.last_deviations,
                    FRAME_WIDTH, 
                    FRAME_HEIGHT
                )
                
                # Update frame for UI display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.last_frame = Image.fromarray(frame_rgb)
                    
        except Exception as e:
            print(f"!!! ERROR in processing thread: {e}")
            import traceback
            traceback.print_exc()
            self.last_feedback = f"Error: {e}"
            self.last_frame = None
            self.last_deviations = set()
            self.is_running = False
            
        finally:
            # Clean up
            self.camera_manager.stop()
            print("DEBUG: process_frames thread finished cleanup")
            
            # Reset UI elements
            self.last_frame = None
            self.last_score = 0.0
            if not self.last_feedback.startswith("Error:"):
                self.last_feedback = "Session stopped."
            self.last_deviations = set()
            
            # Schedule final UI update
            self.after(10, self.update_ui_elements)
            
    def update_ui_elements(self):
        """Update UI with current application state"""
        # Update video feed
        if self.last_frame is not None:
            try:
                img = self.last_frame.resize((FRAME_WIDTH, FRAME_HEIGHT))
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(FRAME_WIDTH, FRAME_HEIGHT))
                self.video_label.configure(image=ctk_image, text="")
                self.video_label.image = ctk_image  # Keep a reference
            except Exception as e:
                print(f"!!! ERROR in update_ui_elements: {e}")
                import traceback
                traceback.print_exc()
                self.video_label.configure(image=None, text="Error displaying frame")
                self.video_label.image = None
        else:
            self.video_label.configure(image=None, text="Camera Feed (Stopped)")
            self.video_label.image = None
            
        # Update score and feedback
        self.score_label.configure(text=f"Score: {self.last_score:.1f}")
        self.feedback_text_label.configure(text=f"Feedback: {self.last_feedback}")
        
        # Set score color
        if self.last_score >= 85:
            self.score_label.configure(text_color="lightgreen")
        elif self.last_score >= 60:
            self.score_label.configure(text_color="yellow")
        else:
            self.score_label.configure(text_color="lightcoral")
            
        # Update Status Label with Pose Number
        if self.is_running and self.pro_data_loaded:
            frame_count = self.motion_player.get_frame_count()
            display_index = self.motion_player.get_display_frame_number()
            self.status_label.configure(text=f"Status: Practicing Pose {display_index}/{frame_count}")
        elif not self.is_running and self.pro_data_loaded:
            self.status_label.configure(
                text=f"Status: Ready ({self.motion_player.get_frame_count()} frames)."
            )
            
        # Reschedule the update ONLY if the session is running
        if self.is_running:
            self.after(33, self.update_ui_elements)  # Aim for ~30 FPS UI updates
            
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
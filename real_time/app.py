import customtkinter as ctk
import cv2
import mediapipe as mp
import numpy as np
import json
import threading
import time
from PIL import Image, ImageTk

# --- Configuration ---
PROFESSIONAL_KEYPOINTS_FILE = "./real_time/professional_keypoints.json"
CAMERA_INDEX = 0
TARGET_FPS = 30 # Match professional video FPS if possible
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
ADVANCE_SCORE_THRESHOLD = 98.0 # Score needed to move to the next pose

# --- MediaPipe Setup ---
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)

# --- Global Variables ---
professional_keypoints = []
is_running = False # General flag for camera/processing thread
current_pro_frame_index = 0 # Index of the professional pose being shown
processing_thread = None
last_frame = None
last_score = 0.0
last_feedback = "Waiting..."
last_deviations = set() # Store names of joints with significant errors

# --- Helper Functions ---
def load_professional_keypoints(filepath):
    global professional_keypoints
    try:
        with open(filepath, 'r') as f:
            professional_keypoints = json.load(f)
        print(f"Loaded {len(professional_keypoints)} frames of professional keypoints.")
        if not professional_keypoints:
             print("Warning: Professional keypoints file is empty.")
             return False
        return True
    except FileNotFoundError:
        print(f"Error: Professional keypoints file not found at {filepath}")
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred loading keypoints: {e}")
        return False

def get_pro_frame_data(frame_index):
    if not professional_keypoints or frame_index < 0 or frame_index >= len(professional_keypoints):
        return None
    # Ensure the loaded data structure matches expectations
    if "keypoints" in professional_keypoints[frame_index]:
        return professional_keypoints[frame_index]["keypoints"]
    else:
        print(f"Warning: Frame {frame_index} in professional data has unexpected format.")
        return None


def calculate_similarity(user_kpts, pro_kpts):
    if not user_kpts or not pro_kpts:
        return 0.0, "No pose detected", set() # Return empty set for deviations

    total_distance = 0
    common_joints = 0
    # Increased threshold slightly for highlighting, adjust as needed
    deviation_threshold = 0.35
    max_possible_dist_per_joint = np.sqrt(1**2 + 1**2 + 1**2)

    feedback_details = []
    deviating_joints = set() # Use a set for efficient lookup

    for joint_name, user_coord in user_kpts.items():
        # Only consider major body joints for feedback/highlighting if desired
        # Example: if joint_name not in ['LEFT_HEEL', 'RIGHT_HEEL', 'LEFT_FOOT_INDEX', 'RIGHT_FOOT_INDEX', ...]: continue
        if joint_name in pro_kpts and pro_kpts[joint_name]:
            pro_coord = pro_kpts[joint_name]
            dist = np.linalg.norm(np.array(user_coord[:3]) - np.array(pro_coord[:3]))
            total_distance += dist
            common_joints += 1

            # Check for significant deviation for highlighting and feedback
            if dist > deviation_threshold:
                 joint_title = joint_name.replace('_', ' ').title()
                 feedback_details.append(f"Check {joint_title}")
                 deviating_joints.add(joint_name) # Add joint name to the set


    if common_joints == 0:
        return 0.0, "Cannot compare poses", set()

    avg_distance = total_distance / common_joints
    normalized_distance = avg_distance / max_possible_dist_per_joint
    score = max(0.0, 100.0 * (1.0 - normalized_distance))

    if not feedback_details:
        feedback = "Good alignment!" if score > 85 else "Keep practicing alignment."
    else:
        feedback = "Corrections needed: " + ", ".join(feedback_details[:2])

    # Return score, feedback text, and the set of deviating joints
    return score, feedback, deviating_joints

def process_frames(app_instance):
    global is_running, last_frame, last_score, last_feedback, current_pro_frame_index, last_deviations
    print("DEBUG: process_frames thread started")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Error: Cannot open camera {CAMERA_INDEX}")
        last_feedback = "Error: Camera unavailable"
        is_running = False # Ensure loop doesn't run
        app_instance.after(100, app_instance.update_ui_elements)
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)

    highlight_color = (0, 0, 255) # Red for highlighting deviations (BGR)
    normal_point_color = (0, 255, 0) # Green for normal points (BGR)
    normal_line_color = (150, 255, 150) # Light Green for normal lines (BGR)

    frame_count = len(professional_keypoints) # Get total frames once

    while is_running: # Keep processing as long as camera should be on
        try:
            loop_start_time = time.time()

            # --- Ensure index is valid before proceeding ---
            if frame_count == 0:
                last_feedback = "No professional frames loaded."
                time.sleep(0.1)
                continue # Skip processing if no pro data

            # Wrap index at the beginning of the loop iteration
            # current_pro_frame_index = current_pro_frame_index % frame_count

            success, frame = cap.read()
            if not success:
                print("DEBUG: cap.read() returned success=False")
                last_feedback = "Error reading frame"
                time.sleep(0.1)
                continue

            # --- Pose Estimation (User) ---
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb.flags.writeable = False
            results = pose.process(frame_rgb)

            # --- Keypoint Extraction & Drawing (User) ---
            user_keypoints = {}
            if results.pose_landmarks:
                for idx, landmark in enumerate(results.pose_landmarks.landmark):
                    landmark_name = mp_pose.PoseLandmark(idx).name
                    user_keypoints[landmark_name] = [landmark.x, landmark.y, landmark.z, landmark.visibility]

                # Draw USER landmarks on the BGR frame
                mp_drawing.draw_landmarks(
                    frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), # User: Orange/Pink
                    mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                )
            else:
                 last_feedback = "No user pose detected"

            # --- Get Professional Keypoints for the CURRENT frame ---
            safe_index = current_pro_frame_index % frame_count
            pro_frame_kpts = get_pro_frame_data(safe_index)

            # --- Comparison (User vs Pro) ---
            if pro_frame_kpts and user_keypoints:
                current_score, current_feedback, current_deviations = calculate_similarity(user_keypoints, pro_frame_kpts)
                last_score = current_score
                last_feedback = current_feedback
                last_deviations = current_deviations # Update the global set
            elif not pro_frame_kpts:
                 last_feedback = f"Pro frame {safe_index} data missing?"
                 last_score = 0.0
                 last_deviations = set() # Clear deviations if no pro data
            else: # No user keypoints detected
                 last_score = 0.0
                 last_deviations = set() # Clear deviations if no user data

            # TODO: Fix display later
            # --- Draw PROFESSIONAL Keypoints and Connections (with Highlighting) ---
            if pro_frame_kpts:
                # Dictionary to store pixel coordinates for drawing lines
                pro_pixel_coords = {}

                # First, draw the points, coloring based on deviation
                for joint_name, pro_coord in pro_frame_kpts.items():
                    if pro_coord: # Check if data exists for this joint
                        # Convert normalized coords to pixel coords
                        px = int(pro_coord[0] * FRAME_WIDTH)
                        py = int(pro_coord[1] * FRAME_HEIGHT)
                        pro_pixel_coords[joint_name] = (px, py) # Store pixel coords

                        # Determine color based on deviation
                        point_color = highlight_color if joint_name in last_deviations else normal_point_color
                        cv2.circle(frame, (px, py), radius=4, color=point_color, thickness=-1) # Draw a circle for the professional keypoint

                # Second, draw the connections, coloring based on deviation
                for connection in mp_pose.POSE_CONNECTIONS:
                    try:
                        # Check if connection elements are integers
                        if isinstance(connection[0], int) and isinstance(connection[1], int):
                             # Convert integer index to PoseLandmark enum
                             start_landmark = mp_pose.PoseLandmark(connection[0])
                             end_landmark = mp_pose.PoseLandmark(connection[1])
                        else:
                             # Assume they are already PoseLandmark enums (standard case)
                             start_landmark = connection[0]
                             end_landmark = connection[1]

                        # Get names from the enum members
                        start_joint_name = start_landmark.name
                        end_joint_name = end_landmark.name

                        # Check if both connected joints were found and drawn
                        if start_joint_name in pro_pixel_coords and end_joint_name in pro_pixel_coords:
                            start_pt = pro_pixel_coords[start_joint_name]
                            end_pt = pro_pixel_coords[end_joint_name]

                            # Determine color based on deviation of either connected joint
                            line_color = highlight_color if (start_joint_name in last_deviations or end_joint_name in last_deviations) else normal_line_color
                            cv2.line(frame, start_pt, end_pt, line_color, thickness=2)

                    except Exception as e:
                        # Print an error if conversion or drawing fails for a specific connection
                        print(f"Error processing connection {connection}: {e}")
                        # Continue to the next connection instead of crashing the thread
                        continue

            # --- Prepare Frame for Display ---
            # Convert the frame (which now has BOTH user and pro landmarks) to RGB
            frame_for_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            current_pil_image = Image.fromarray(frame_for_display)
            last_frame = current_pil_image # Update global variable

            # --- Frame Rate Control (Still needed for smooth camera feed) ---
            elapsed_time = time.time() - loop_start_time
            sleep_time = (1.0 / TARGET_FPS) - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)

            # --- Auto-Increment Frame Index ---
            if last_score >= ADVANCE_SCORE_THRESHOLD:
                print(f"DEBUG: Pose {safe_index + 1} matched! Score: {last_score:.1f}. Advancing.")
                current_pro_frame_index += 1

        except Exception as e:
            print(f"!!! ERROR in processing thread: {e}")
            import traceback
            traceback.print_exc()
            last_feedback = f"Error: {e}"
            last_frame = None # Clear frame on error
            print("DEBUG: last_frame set to None due to exception")
            last_deviations = set() # Clear deviations on error
            is_running = False

    # --- Cleanup ---
    cap.release()
    print("DEBUG: process_frames thread finished cleanup")
    print("Processing thread stopped.")
    # Reset UI elements after stopping
    last_frame = None
    last_score = 0.0
    # Keep the last feedback if it was an error, otherwise reset
    if last_feedback.startswith("Error:") :
         pass # Keep error message
    else:
         last_feedback = "Session stopped."
    last_deviations = set() # Clear deviations on stop
    # Schedule a final UI update
    app_instance.after(10, app_instance.update_ui_elements)


# --- GUI Application ---
class DanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Real-time Dance Instructor")
        self.geometry("800x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Video row

        # --- Top Control Frame ---
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.control_frame.grid_columnconfigure(2, weight=1) # Make status label expand

        self.start_stop_button = ctk.CTkButton(self.control_frame, text="Start Practice", command=self.toggle_session) # Renamed button
        self.start_stop_button.grid(row=0, column=0, padx=5)

        self.load_pro_button = ctk.CTkButton(self.control_frame, text="Load Pro Dance", command=self.load_pro_data_action)
        self.load_pro_button.grid(row=0, column=1, padx=5)

        self.status_label = ctk.CTkLabel(self.control_frame, text="Status: Idle. Load Pro Dance first.", anchor="w")
        self.status_label.grid(row=0, column=2, padx=10, sticky="ew") # Adjusted column

        # --- Video Display ---
        self.video_label = ctk.CTkLabel(self, text="Camera Feed", fg_color="gray20")
        self.video_label.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # --- Feedback Frame ---
        self.feedback_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.feedback_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.feedback_frame.grid_columnconfigure(0, weight=1)

        self.score_label = ctk.CTkLabel(self.feedback_frame, text="Score: --", font=ctk.CTkFont(size=18, weight="bold"))
        self.score_label.grid(row=0, column=0, padx=5, sticky="w")

        self.feedback_text_label = ctk.CTkLabel(self.feedback_frame, text="Feedback: Waiting...", anchor="w", justify="left")
        self.feedback_text_label.grid(row=1, column=0, padx=5, sticky="ew")

        # --- Load initial data ---
        self.pro_data_loaded = False
        # self.load_pro_data_action() # Optionally load automatically on start

        # --- Start UI update loop ---
        self.update_ui_elements()

        # --- Handle window closing ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)


    def load_pro_data_action(self):
        global professional_keypoints, current_pro_frame_index
        # In a real app, you'd use a file dialog
        # from tkinter import filedialog
        # filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        filepath = PROFESSIONAL_KEYPOINTS_FILE # Using constant for now
        if filepath:
            if load_professional_keypoints(filepath):
                self.status_label.configure(text=f"Status: Pro data loaded ({len(professional_keypoints)} frames). Ready.")
                self.pro_data_loaded = True
                current_pro_frame_index = 0 # Reset index on load
            else:
                self.status_label.configure(text="Status: Error loading pro data.")
                self.pro_data_loaded = False
        else:
             self.status_label.configure(text="Status: Pro data loading cancelled.")
             self.pro_data_loaded = False


    def toggle_session(self):
        global is_running, processing_thread, current_pro_frame_index
        if not self.pro_data_loaded or not professional_keypoints: # Added check for empty keypoints
             self.status_label.configure(text="Status: Please load valid professional data first!")
             return

        if is_running: # If running, stop it
            is_running = False
            self.start_stop_button.configure(text="Start Practice") # Changed text
            self.load_pro_button.configure(state="normal")
            self.status_label.configure(text="Status: Stopping...")
            self.after(100, self.check_thread_join)

        else: # If not running, start continuous playback
            is_running = True
            current_pro_frame_index = 0 # Start from the first frame
            self.start_stop_button.configure(text="Stop Practice") # Changed text
            self.load_pro_button.configure(state="disabled")
            self.status_label.configure(text="Status: Session Running") # Simplified status
            # Start processing thread
            processing_thread = threading.Thread(target=process_frames, args=(self,), daemon=True)
            processing_thread.start()
            self.update_ui_elements() # Kickstart UI updates

    def check_thread_join(self):
         global processing_thread
         if processing_thread is not None and processing_thread.is_alive():
              print("Waiting for processing thread to finish...")
              self.after(100, self.check_thread_join) # Check again shortly
         else:
              print("Processing thread has finished.")
              processing_thread = None
              self.status_label.configure(text="Status: Idle.")


    def update_ui_elements(self):
        # print("DEBUG: update_ui_elements called") # <-- Optional: Check if function runs
        print(f"DEBUG: update_ui_elements sees last_frame is None: {last_frame is None}") # <-- Add this check

        # Update video feed (shows user and the STATIC pro pose)
        if last_frame is not None:
            try:
                # print("DEBUG: update_ui_elements - trying to update image") # <-- Add
                img = last_frame.resize((FRAME_WIDTH, FRAME_HEIGHT))
                # Create the CTkImage object
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(FRAME_WIDTH, FRAME_HEIGHT))
                # Configure the label AND store a reference on the label itself
                self.video_label.configure(image=ctk_image, text="")
                self.video_label.image = ctk_image # Keep a reference!
                # print("DEBUG: update_ui_elements - image updated successfully") # <-- Add
            except Exception as e:
                 print(f"!!! ERROR in update_ui_elements: {e}") # <-- Check console for this!
                 import traceback
                 traceback.print_exc() # Print full traceback for UI update errors
                 self.video_label.configure(image=None, text="Error displaying frame")
                 self.video_label.image = None # Clear reference on error

        else:
            # print("DEBUG: update_ui_elements - last_frame is None, showing placeholder") # <-- Add
            # Optionally display a placeholder when not running
            self.video_label.configure(image=None, text="Camera Feed (Stopped)")
            self.video_label.image = None # Clear reference if no frame

        # Update score and feedback (reflects comparison to current_pro_frame_index)
        self.score_label.configure(text=f"Score: {last_score:.1f}")
        # Optionally add frame number to feedback if desired
        # feedback_str = f"Feedback (Frame {current_pro_frame_index}): {last_feedback}"
        feedback_str = f"Feedback: {last_feedback}"
        self.feedback_text_label.configure(text=feedback_str)

        # Set score color
        if last_score >= 85:
            self.score_label.configure(text_color="lightgreen")
        elif last_score >= 60:
            self.score_label.configure(text_color="yellow")
        else:
            self.score_label.configure(text_color="lightcoral")

        # Update Status Label with Pose Number
        if is_running and professional_keypoints:
            frame_count = len(professional_keypoints)
            # Use modulo for display index to handle wrapping correctly
            display_index = (current_pro_frame_index % frame_count) + 1
            self.status_label.configure(text=f"Status: Practicing Pose {display_index}/{frame_count}")
        elif not is_running and self.pro_data_loaded:
             self.status_label.configure(text=f"Status: Ready ({len(professional_keypoints)} frames).")

        # Reschedule the update ONLY if the session is running
        if is_running:
            self.after(33, self.update_ui_elements) # Aim for ~30 FPS UI updates

    def on_closing(self):
        global is_running
        print("Closing application...")
        if is_running:
            is_running = False # Signal thread to stop
            # Give thread a moment to stop before destroying window
            if processing_thread is not None:
                 processing_thread.join(timeout=0.5) # Wait max 0.5 sec
        self.destroy()


if __name__ == "__main__":
    app = DanceApp()
    app.mainloop()
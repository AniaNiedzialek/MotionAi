import customtkinter as ctk
import cv2
import mediapipe as mp
import numpy as np
import json
import threading
import time
import os
import sqlite3
from PIL import Image, ImageTk
from database import MotionDatabase
from tkinter import filedialog

class MotionUploadDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Setup window
        self.title("Upload New Motion")
        self.geometry("700x600")
        self.resizable(True, True)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Set up variables
        self.db = MotionDatabase()
        self.categories = self.db.get_categories()
        self.recorded_frames = []
        self.is_recording = False
        self.recording_thread = None
        self.frame_count = 0
        self.selected_file = None
        
        # Source selection
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_view.add("Record from Camera")
        self.tab_view.add("Upload Video File")
        
        # Record from Camera tab
        self.camera_tab = self.tab_view.tab("Record from Camera")
        self.setup_camera_tab()
        
        # Upload Video File tab
        self.file_tab = self.tab_view.tab("Upload Video File")
        self.setup_file_tab()
        
        # Motion details frame
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.pack(fill="x", padx=10, pady=10)
        self.setup_details_frame()
        
        # Control buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        self.save_button = ctk.CTkButton(
            self.button_frame, 
            text="Save Motion", 
            state="disabled",
            command=self.save_motion
        )
        self.save_button.pack(side="right", padx=5, pady=5)
        
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            command=self.on_cancel
        )
        self.cancel_button.pack(side="left", padx=5, pady=5)
        
    def setup_camera_tab(self):
        # Camera preview
        self.camera_frame = ctk.CTkFrame(self.camera_tab)
        self.camera_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.preview_label = ctk.CTkLabel(self.camera_frame, text="Camera Preview")
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Control buttons
        self.camera_controls = ctk.CTkFrame(self.camera_tab)
        self.camera_controls.pack(fill="x", padx=10, pady=10)
        
        self.record_button = ctk.CTkButton(
            self.camera_controls,
            text="Start Recording",
            command=self.toggle_recording
        )
        self.record_button.pack(side="left", padx=5, pady=5)
        
        self.frame_count_label = ctk.CTkLabel(self.camera_controls, text="Frames: 0")
        self.frame_count_label.pack(side="right", padx=5, pady=5)
        
    def setup_file_tab(self):
        # File selection
        self.file_frame = ctk.CTkFrame(self.file_tab)
        self.file_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.file_label = ctk.CTkLabel(
            self.file_frame, 
            text="Select a video file to upload",
            font=ctk.CTkFont(size=14)
        )
        self.file_label.pack(pady=(30, 10))
        
        self.file_path_label = ctk.CTkLabel(
            self.file_frame,
            text="No file selected",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.file_path_label.pack(pady=5)
        
        self.browse_button = ctk.CTkButton(
            self.file_frame,
            text="Browse...",
            command=self.browse_file
        )
        self.browse_button.pack(pady=20)
        
        self.process_button = ctk.CTkButton(
            self.file_frame,
            text="Process Video",
            state="disabled",
            command=self.process_video_file
        )
        self.process_button.pack(pady=5)
        
        self.file_status_label = ctk.CTkLabel(
            self.file_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.file_status_label.pack(pady=10)
        
    def setup_details_frame(self):
        # Motion name
        name_frame = ctk.CTkFrame(self.details_frame)
        name_frame.pack(fill="x", pady=5)
        
        name_label = ctk.CTkLabel(name_frame, text="Motion Name:")
        name_label.pack(side="left", padx=5)
        
        self.name_entry = ctk.CTkEntry(name_frame, width=250)
        self.name_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Category selection
        cat_frame = ctk.CTkFrame(self.details_frame)
        cat_frame.pack(fill="x", pady=5)
        
        cat_label = ctk.CTkLabel(cat_frame, text="Category:")
        cat_label.pack(side="left", padx=5)
        
        self.category_var = ctk.StringVar(value="dance" if "dance" in self.categories else "")
        
        # If we have existing categories, use them, otherwise allow custom input
        if self.categories:
            self.category_combo = ctk.CTkComboBox(
                cat_frame,
                values=self.categories,
                variable=self.category_var,
                width=150
            )
            self.category_combo.pack(side="left", padx=5)
            
            # Add new category button
            self.add_cat_button = ctk.CTkButton(
                cat_frame,
                text="+",
                width=30,
                command=self.add_new_category
            )
            self.add_cat_button.pack(side="left", padx=5)
        else:
            self.category_entry = ctk.CTkEntry(cat_frame, width=150, textvariable=self.category_var)
            self.category_entry.pack(side="left", padx=5)
        
    def add_new_category(self):
        """Show dialog to add a new category"""
        dialog = ctk.CTkInputDialog(
            text="Enter new category name:", 
            title="New Category"
        )
        new_category = dialog.get_input()
        
        if new_category and new_category.strip():
            # Add to database
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (new_category,))
            conn.commit()
            conn.close()
            
            # Update combo box
            self.categories = self.db.get_categories()
            self.category_combo.configure(values=self.categories)
            self.category_var.set(new_category)
            
    def toggle_recording(self):
        """Start or stop recording from camera"""
        if self.is_recording:
            # Stop recording
            self.is_recording = False
            self.record_button.configure(text="Start Recording")
            self.save_button.configure(state="normal")
        else:
            # Start recording
            self.recorded_frames = []
            self.frame_count = 0
            self.is_recording = True
            self.record_button.configure(text="Stop Recording")
            self.save_button.configure(state="disabled")
            
            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self.record_from_camera,
                daemon=True
            )
            self.recording_thread.start()
    
    def record_from_camera(self):
        """Thread function to record poses from camera"""
        # MediaPipe setup
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)
        
        # Camera setup
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Cannot open camera")
            return
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        try:
            while self.is_recording:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Process frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(frame_rgb)
                
                # Extract keypoints
                if results.pose_landmarks:
                    keypoints = {}
                    for idx, landmark in enumerate(results.pose_landmarks.landmark):
                        landmark_name = mp_pose.PoseLandmark(idx).name
                        keypoints[landmark_name] = [landmark.x, landmark.y, landmark.z, landmark.visibility]
                    
                    # Store frame data
                    self.recorded_frames.append({
                        "frame_index": self.frame_count,
                        "keypoints": keypoints
                    })
                    self.frame_count += 1
                    
                    # Update UI
                    self.update_frame_count()
                
                # Draw landmarks
                if results.pose_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                    )
                
                # Update preview
                self.update_preview(frame)
                
                # Frame rate control
                time.sleep(1/30)
                
        finally:
            cap.release()
            pose.close()
    
    def update_preview(self, frame):
        """Update the camera preview"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(image=img)
        
        # Update label
        self.preview_label.configure(image=photo, text="")
        self.preview_label.image = photo
    
    def update_frame_count(self):
        """Update the frame count label"""
        self.frame_count_label.configure(text=f"Frames: {self.frame_count}")
    
    def browse_file(self):
        """Open file browser to select a video file"""
        filetypes = (
            ('Video files', '*.mp4 *.avi *.mov'),
            ('All files', '*.*')
        )
        
        filename = filedialog.askopenfilename(
            title='Select a video file',
            initialdir='/',
            filetypes=filetypes
        )
        
        if filename:
            self.selected_file = filename
            self.file_path_label.configure(text=os.path.basename(filename))
            self.process_button.configure(state="normal")
    
    def process_video_file(self):
        """Process the selected video file"""
        if not self.selected_file:
            return
        
        self.file_status_label.configure(text="Processing video...", text_color="orange")
        
        # Start processing in a thread
        threading.Thread(
            target=self._process_video_thread,
            daemon=True
        ).start()
    
    def _process_video_thread(self):
        """Thread function to process a video file"""
        try:
            # MediaPipe setup
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)
            
            # Open video
            cap = cv2.VideoCapture(self.selected_file)
            if not cap.isOpened():
                self.after(0, lambda: self.file_status_label.configure(
                    text="Error opening video file!", text_color="red"
                ))
                return
                
            # Reset frames
            self.recorded_frames = []
            self.frame_count = 0
            
            # Process every other frame
            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every other frame to reduce quantity
                if frame_index % 2 == 0:
                    # Process frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose.process(frame_rgb)
                    
                    # Extract keypoints
                    if results.pose_landmarks:
                        keypoints = {}
                        for idx, landmark in enumerate(results.pose_landmarks.landmark):
                            landmark_name = mp_pose.PoseLandmark(idx).name
                            keypoints[landmark_name] = [landmark.x, landmark.y, landmark.z, landmark.visibility]
                        
                        # Store frame data
                        self.recorded_frames.append({
                            "frame_index": self.frame_count,
                            "keypoints": keypoints
                        })
                        self.frame_count += 1
                
                frame_index += 1
                
                # Update UI periodically
                if frame_index % 30 == 0:
                    self.after(0, lambda count=self.frame_count: self.file_status_label.configure(
                        text=f"Processed {count} frames...", text_color="orange"
                    ))
            
            cap.release()
            pose.close()
            
            # Enable save button if frames were extracted
            if self.frame_count > 0:
                self.after(0, lambda: self.file_status_label.configure(
                    text=f"Extracted {self.frame_count} frames", text_color="green"
                ))
                self.after(0, lambda: self.save_button.configure(state="normal"))
                
                # Auto-populate name from filename
                filename = os.path.basename(self.selected_file)
                name_without_ext = os.path.splitext(filename)[0]
                name_formatted = " ".join(word.capitalize() for word in name_without_ext.split('_'))
                self.after(0, lambda: self.name_entry.delete(0, 'end'))
                self.after(0, lambda: self.name_entry.insert(0, name_formatted))
            else:
                self.after(0, lambda: self.file_status_label.configure(
                    text="No pose data detected in video!", text_color="red"
                ))
                
        except Exception as e:
            self.after(0, lambda: self.file_status_label.configure(
                text=f"Error: {str(e)}", text_color="red"
            ))
    
    def save_motion(self):
        """Save the recorded motion to database"""
        # Validate inputs
        motion_name = self.name_entry.get().strip()
        if not motion_name:
            ctk.CTkMessagebox(
                title="Validation Error", 
                message="Please enter a motion name",
                icon="cancel"
            )
            return
            
        # Get category
        if hasattr(self, 'category_combo'):
            category = self.category_var.get()
        else:
            category = self.category_entry.get().strip()
            
        if not category:
            ctk.CTkMessagebox(
                title="Validation Error",
                message="Please select or enter a category",
                icon="cancel"
            )
            return
            
        # Validate frames
        if not self.recorded_frames:
            ctk.CTkMessagebox(
                title="Validation Error",
                message="No motion data recorded!",
                icon="cancel"
            )
            return
            
        # Save to database
        motion_id = self.db.add_motion(
            name=motion_name,
            category=category,
            keypoints_data=self.recorded_frames
        )
        
        if motion_id:
            ctk.CTkMessagebox(
                title="Success",
                message=f"Motion '{motion_name}' saved successfully!",
                icon="check"
            )
            self.destroy()
        else:
            ctk.CTkMessagebox(
                title="Error",
                message="Failed to save motion!",
                icon="cancel"
            )
    
    def on_cancel(self):
        """Cancel and close dialog"""
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
            
        self.destroy()
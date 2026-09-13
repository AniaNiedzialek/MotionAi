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
from tkinter import messagebox


class MotionUploadDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        # --- Window setup ---
        self.title("Upload New Motion")
        self.geometry("900x750")
        self.resizable(True, True)

        # Modal dialog
        self.transient(parent)
        self.grab_set()

        # --- State ---
        self.db = MotionDatabase()
        self.categories = self.db.get_categories()
        self.recorded_frames = []
        self.is_recording = False
        self.recording_thread = None
        self.frame_count = 0
        self.selected_file = None
        self._closing = False  # guard for late UI callbacks

        # --- Tabs: camera / file ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_view.add("Record from Camera")
        self.tab_view.add("Upload Video File")

        self.camera_tab = self.tab_view.tab("Record from Camera")
        self.setup_camera_tab()

        self.file_tab = self.tab_view.tab("Upload Video File")
        self.setup_file_tab()

        # --- Motion details ---
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.pack(fill="x", padx=10, pady=10)
        self.setup_details_frame()

        # --- Bottom buttons ---
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=10, pady=10)

        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="Save Motion",
            state="disabled",
            command=self.save_motion,
        )
        self.save_button.pack(side="right", padx=5, pady=5)

        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", command=self.on_cancel
        )
        self.cancel_button.pack(side="left", padx=5, pady=5)

        # --- Shortcuts ---
        self.bind("<space>", lambda e: self.toggle_recording())
        self.bind(
            "<Return>",
            lambda e: self.save_button.invoke()
            if str(self.save_button.cget("state")) == "normal"
            else None,
        )
        self.bind("<Escape>", lambda e: self.on_cancel())

    # ---------- UI builders ----------

    def setup_camera_tab(self):
        # Preview
        self.camera_frame = ctk.CTkFrame(self.camera_tab)
        self.camera_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.preview_label = ctk.CTkLabel(self.camera_frame, text="Camera Preview")
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Controls
        self.camera_controls = ctk.CTkFrame(self.camera_tab)
        self.camera_controls.pack(fill="x", padx=10, pady=10)

        self.record_button = ctk.CTkButton(
            self.camera_controls, text="Start Recording", command=self.toggle_recording
        )
        self.record_button.pack(side="left", padx=5, pady=5)

        self.frame_count_label = ctk.CTkLabel(self.camera_controls, text="Frames: 0")
        self.frame_count_label.pack(side="right", padx=5, pady=5)

    def setup_file_tab(self):
        self.file_frame = ctk.CTkFrame(self.file_tab)
        self.file_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.file_label = ctk.CTkLabel(
            self.file_frame, text="Select a video file to upload", font=ctk.CTkFont(size=14)
        )
        self.file_label.pack(pady=(30, 10))

        self.file_path_label = ctk.CTkLabel(
            self.file_frame, text="No file selected", font=ctk.CTkFont(size=12), text_color="gray70"
        )
        self.file_path_label.pack(pady=5)

        self.browse_button = ctk.CTkButton(self.file_frame, text="Browse...", command=self.browse_file)
        self.browse_button.pack(pady=20)

        self.process_button = ctk.CTkButton(
            self.file_frame, text="Process Video", state="disabled", command=self.process_video_file
        )
        self.process_button.pack(pady=5)

        self.file_status_label = ctk.CTkLabel(self.file_frame, text="", font=ctk.CTkFont(size=12))
        self.file_status_label.pack(pady=10)

        # Quality settings
        self.quality_frame = ctk.CTkFrame(self.file_tab)
        self.quality_frame.pack(fill="x", padx=10, pady=5)

        fps_label = ctk.CTkLabel(self.quality_frame, text="Target FPS:")
        fps_label.pack(side="left", padx=5)

        self.target_fps_var = ctk.IntVar(value=15)
        self.target_fps_slider = ctk.CTkSlider(
            self.quality_frame, from_=5, to=30, number_of_steps=25, variable=self.target_fps_var, width=150
        )
        self.target_fps_slider.pack(side="left", padx=5)

        self.fps_value_label = ctk.CTkLabel(self.quality_frame, text="15")
        self.fps_value_label.pack(side="left", padx=5)
        self.target_fps_slider.configure(command=self._update_fps_label)

        conf_frame = ctk.CTkFrame(self.file_tab)
        conf_frame.pack(fill="x", padx=10, pady=5)

        conf_label = ctk.CTkLabel(conf_frame, text="Min. Pose Confidence:")
        conf_label.pack(side="left", padx=5)

        self.min_confidence_var = ctk.DoubleVar(value=0.6)
        self.confidence_slider = ctk.CTkSlider(
            conf_frame, from_=0.3, to=0.9, number_of_steps=12, variable=self.min_confidence_var, width=150
        )
        self.confidence_slider.pack(side="left", padx=5)

        self.conf_value_label = ctk.CTkLabel(conf_frame, text="0.6")
        self.conf_value_label.pack(side="left", padx=5)
        self.confidence_slider.configure(command=self._update_conf_label)

        self.interpolate_var = ctk.BooleanVar(value=True)
        self.interpolate_check = ctk.CTkCheckBox(
            self.file_tab, text="Interpolate missing poses", variable=self.interpolate_var
        )
        self.interpolate_check.pack(pady=5)

    def setup_details_frame(self):
        name_frame = ctk.CTkFrame(self.details_frame)
        name_frame.pack(fill="x", pady=5)

        name_label = ctk.CTkLabel(name_frame, text="Motion Name:")
        name_label.pack(side="left", padx=5)

        self.name_entry = ctk.CTkEntry(name_frame, width=250)
        self.name_entry.pack(side="left", padx=5, fill="x", expand=True)

        cat_frame = ctk.CTkFrame(self.details_frame)
        cat_frame.pack(fill="x", pady=5)

        cat_label = ctk.CTkLabel(cat_frame, text="Category:")
        cat_label.pack(side="left", padx=5)

        self.category_var = ctk.StringVar(value="dance" if "dance" in self.categories else "")

        if self.categories:
            self.category_combo = ctk.CTkComboBox(
                cat_frame, values=self.categories, variable=self.category_var, width=150
            )
            self.category_combo.pack(side="left", padx=5)

            self.add_cat_button = ctk.CTkButton(
                cat_frame, text="+", width=30, command=self.add_new_category
            )
            self.add_cat_button.pack(side="left", padx=5)
        else:
            self.category_entry = ctk.CTkEntry(cat_frame, width=150, textvariable=self.category_var)
            self.category_entry.pack(side="left", padx=5)

    # ---------- Helpers ----------

    def ui_alive(self):
        """Return True if the dialog and preview label still exist."""
        return self.winfo_exists() and hasattr(self, "preview_label") and self.preview_label.winfo_exists()

    def safe_after(self, func):
        """Schedule a UI callback only if the dialog is still alive."""
        if self.ui_alive():
            try:
                self.after(0, func)
            except Exception:
                pass

    # ---------- Actions ----------

    def add_new_category(self):
        dialog = ctk.CTkInputDialog(text="Enter new category name:", title="New Category")
        new_category = dialog.get_input()

        if new_category and new_category.strip():
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (new_category,))
            conn.commit()
            conn.close()

            self.categories = self.db.get_categories()
            self.category_combo.configure(values=self.categories)
            self.category_var.set(new_category)

    def toggle_recording(self):
        """Start or stop recording from camera."""
        if self.is_recording:
            # --- STOP ---
            self.is_recording = False
            self.record_button.configure(text="Start Recording", state="disabled")

            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=1.0)

            if self.recorded_frames:
                self.save_button.configure(state="normal")
            else:
                self.save_button.configure(state="disabled")

            self.record_button.configure(state="normal")
        else:
            # --- START ---
            self.recorded_frames = []
            self.frame_count = 0
            self.is_recording = True
            self.record_button.configure(text="Stop Recording")
            self.save_button.configure(state="disabled")

            self.recording_thread = threading.Thread(target=self.record_from_camera, daemon=True)
            self.recording_thread.start()

    def record_from_camera(self):
        """Thread function to record poses from camera."""
        import traceback

        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)

        # Prefer AVFoundation on macOS
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(0)
        except Exception:
            cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: Cannot open camera")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        try:
            while self.is_recording and not self._closing:
                ok, frame = cap.read()
                if not ok or frame is None:
                    time.sleep(0.01)
                    continue

                # Pose processing
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                try:
                    results = pose.process(frame_rgb)
                except Exception:
                    traceback.print_exc()
                    continue

                keypoints = None
                frame_vis = frame
                if results.pose_landmarks:
                    keypoints = {}
                    for idx, landmark in enumerate(results.pose_landmarks.landmark):
                        name = mp_pose.PoseLandmark(idx).name
                        keypoints[name] = [landmark.x, landmark.y, landmark.z, landmark.visibility]

                    frame_vis = frame.copy()
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame_vis, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                    )

                # Save only if valid keypoints
                if keypoints is not None:
                    self.recorded_frames.append(
                        {"frame_index": self.frame_count, "keypoints": keypoints}
                    )
                    self.frame_count += 1
                    self.safe_after(self.update_frame_count)

                # Update preview on UI thread
                self.safe_after(lambda f=frame_vis.copy(): self.update_preview(f))

                time.sleep(1 / 30.0)

        finally:
            cap.release()
            pose.close()

    # ---------- UI updates ----------

    def update_preview(self, frame):
        """Update the camera preview safely."""
        if not self.ui_alive():
            return
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image=img)
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo
        except Exception:
            # ignore late updates during shutdown
            pass

    def update_frame_count(self):
        self.frame_count_label.configure(text=f"Frames: {self.frame_count}")

    # ---------- File workflow ----------

    def browse_file(self):
        filetypes = (("Video files", "*.mp4 *.avi *.mov"), ("All files", "*.*"))
        filename = filedialog.askopenfilename(title="Select a video file", initialdir="/", filetypes=filetypes)

        if filename:
            self.selected_file = filename
            self.file_path_label.configure(text=os.path.basename(filename))
            self.process_button.configure(state="normal")

    def process_video_file(self):
        if not self.selected_file:
            return

        self.file_status_label.configure(text="Processing video...", text_color="orange")
        threading.Thread(target=self._process_video_thread, daemon=True).start()

    def _process_video_thread(self):
        """Process the selected video file (adaptive sampling)."""
        try:
            target_fps = self.target_fps_var.get()
            min_confidence = self.min_confidence_var.get()
            use_interpolation = self.interpolate_var.get()

            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(
                min_detection_confidence=min_confidence, min_tracking_confidence=min_confidence
            )

            cap = cv2.VideoCapture(self.selected_file)
            if not cap.isOpened():
                self.safe_after(lambda: self.file_status_label.configure(
                    text="Error opening video file!", text_color="red"
                ))
                return

            video_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_rate = max(1, round(video_fps / target_fps))

            expected_frames = total_frames // sample_rate
            self.safe_after(lambda: self.file_status_label.configure(
                text=f"Processing video ({expected_frames} frames expected)...",
                text_color="orange"
            ))

            self.recorded_frames = []
            self.frame_count = 0

            last_keypoints = None
            frames_since_detection = 0

            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_index % sample_rate == 0:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose.process(frame_rgb)

                    if results.pose_landmarks:
                        keypoints = {}
                        for idx, landmark in enumerate(results.pose_landmarks.landmark):
                            landmark_name = mp_pose.PoseLandmark(idx).name
                            keypoints[landmark_name] = [
                                landmark.x, landmark.y, landmark.z, landmark.visibility
                            ]

                        self.recorded_frames.append(
                            {"frame_index": self.frame_count, "keypoints": keypoints}
                        )
                        last_keypoints = keypoints
                        frames_since_detection = 0
                        self.frame_count += 1

                    elif last_keypoints is not None and use_interpolation:
                        frames_since_detection += 1
                        if frames_since_detection <= 3:
                            self.recorded_frames.append(
                                {"frame_index": self.frame_count, "keypoints": last_keypoints.copy()}
                            )
                            self.frame_count += 1

                frame_index += 1

                if frame_index % 30 == 0:
                    progress = min(100, int((frame_index / total_frames) * 100))
                    self.safe_after(
                        lambda p=progress, c=self.frame_count: self.file_status_label.configure(
                            text=f"Processing: {p}% ({c} frames captured)...", text_color="orange"
                        )
                    )

            if use_interpolation and len(self.recorded_frames) >= 2:
                self.safe_after(lambda: self.file_status_label.configure(
                    text="Performing pose interpolation...", text_color="orange"
                ))
                self._interpolate_between_keyframes()

            cap.release()
            pose.close()

            if self.frame_count > 0:
                self.safe_after(lambda: self.file_status_label.configure(
                    text=f"Extracted {self.frame_count} frames", text_color="green"
                ))
                self.safe_after(lambda: self.save_button.configure(state="normal"))

                filename = os.path.basename(self.selected_file)
                name_without_ext = os.path.splitext(filename)[0]
                name_formatted = " ".join(word.capitalize() for word in name_without_ext.split("_"))
                self.safe_after(lambda: self.name_entry.delete(0, "end"))
                self.safe_after(lambda: self.name_entry.insert(0, name_formatted))
            else:
                self.safe_after(lambda: self.file_status_label.configure(
                    text="No pose data detected in video!", text_color="red"
                ))

        except Exception as e:
            import traceback
            traceback.print_exc()
            # bind the message now, e is unbound by the time the callback runs
            self.safe_after(lambda msg=str(e): self.file_status_label.configure(text=f"Error: {msg}", text_color="red"))

    # ---------- Interpolation ----------

    def _interpolate_between_keyframes(self):
        keyframes = []
        frame_to_idx = {}

        for i, frame in enumerate(self.recorded_frames):
            frame_to_idx[frame["frame_index"]] = i
            keyframes.append(frame)

        if len(keyframes) < 2:
            return

        def interp(val1, val2, fraction):
            return val1 + (val2 - val1) * fraction

        new_frames = []
        for i in range(len(keyframes) - 1):
            start_frame = keyframes[i]
            end_frame = keyframes[i + 1]
            start_idx = start_frame["frame_index"]
            end_idx = end_frame["frame_index"]

            if end_idx - start_idx <= 1:
                new_frames.append(start_frame)
                continue

            new_frames.append(start_frame)

            num_insertions = end_idx - start_idx - 1
            if num_insertions > 0 and num_insertions < 10:
                start_kpts = start_frame["keypoints"]
                end_kpts = end_frame["keypoints"]
                common_landmarks = set(start_kpts.keys()).intersection(end_kpts.keys())

                for j in range(1, num_insertions + 1):
                    fraction = j / (num_insertions + 1)
                    interp_keypoints = {}
                    for landmark in common_landmarks:
                        s = start_kpts[landmark]
                        e = end_kpts[landmark]
                        interp_keypoints[landmark] = [
                            interp(s[0], e[0], fraction),
                            interp(s[1], e[1], fraction),
                            interp(s[2], e[2], fraction),
                            interp(s[3], e[3], fraction),
                        ]
                    new_frames.append({"frame_index": start_idx + j, "keypoints": interp_keypoints})

        if keyframes:
            new_frames.append(keyframes[-1])

        self.recorded_frames = sorted(new_frames, key=lambda x: x["frame_index"])
        self.frame_count = len(self.recorded_frames)

    # ---------- Save / Close ----------

    def save_motion(self):
        """Save the recorded motion to database."""
        motion_name = self.name_entry.get().strip()
        if not motion_name:
            messagebox.showerror("Validation Error", "Please enter a motion name")
            return

        if hasattr(self, "category_combo"):
            category = self.category_var.get()
        else:
            category = self.category_entry.get().strip()

        if not category:
            messagebox.showerror("Validation Error", "Please select or enter a category")
            return

        if not self.recorded_frames:
            messagebox.showerror("Validation Error", "No motion data recorded!")
            return

        motion_id = self.db.add_motion(name=motion_name, category=category, keypoints_data=self.recorded_frames)

        if motion_id:
            messagebox.showinfo("Success", f"Motion '{motion_name}' saved successfully!")

            # Clean shutdown before closing dialog
            self._closing = True
            self.is_recording = False
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=1.0)
            # Optionally notify parent to refresh (if implemented)
            if hasattr(self.master, "refresh_motion_list"):
                try:
                    self.master.refresh_motion_list()
                except Exception:
                    pass
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to save motion!")

    def on_cancel(self):
        """Cancel and close dialog."""
        self._closing = True
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
        self.destroy()

    # ---------- Slider labels ----------

    def _update_fps_label(self, value):
        self.fps_value_label.configure(text=f"{int(value)}")

    def _update_conf_label(self, value):
        self.conf_value_label.configure(text=f"{value:.1f}")

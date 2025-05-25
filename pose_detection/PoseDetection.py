import cv2
import mediapipe as mp
import numpy as np
import os
import speech_recognition as sr
import threading

# Initialize MediaPipe Pose and Hands
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands


class PoseEstimationService:
    def __init__(self):
        self.pose = mp_pose.Pose()
        self.hands = mp_hands.Hands()
        self.keypoints_data = self.initialize_keypoints_data()
        self.frame_counter = 0
        self.is_running = True  # Flag to control the loop

        # Load existing file names to avoid conflicts
        self.existing_filenames = self.load_existing_filenames()

        # Set the output video file name
        self.video_file = self.generate_filename("user.avi")

        # Set the keypoints file name
        self.keypoints_file = self.generate_filename("user.txt")
    
    def load_existing_filenames(self):
        if os.path.exists("last_saved_filename.txt"):
            with open("last_saved_filename.txt", 'r') as f:
                return {line.strip() for line in f} # Use a set for fast look up
        return set()

    def generate_filename(self, base_filename):
        counter = 0
        original_base_filename = base_filename

        # Check if the base file name exists
        while base_filename in self.existing_filenames or os.path.exists(base_filename):
            base_name, extension = os.path.splitext(original_base_filename)
            counter += 1
            base_filename = f"{base_name}_{counter}{extension}"

        # Add the newly generated filename to the existing filenames set
        self.existing_filenames.add(base_filename)

        return base_filename

    def initialize_keypoints_data(self):
        return {
            "nose": [],
            "left_eye": [],
            "right_eye": [],
            "left_ear": [],
            "right_ear": [],
            "shoulder_left": [],
            "shoulder_right": [],
            "elbow_left": [],
            "elbow_right": [],
            "wrist_left": [],
            "wrist_right": [],
            "hip_left": [],
            "hip_right": [],
            "knee_left": [],
            "knee_right": [],
            "ankle_left": [],
            "ankle_right": [],
            "heel_left": [],
            "heel_right": [],
            "foot_index_left": [],
            "foot_index_right": [],
            "left_index_finger_tip": [], "right_index_finger_tip": [],
            "left_thumb_tip": [], "right_thumb_tip": []
        }

    def start_video_capture(self):
        cap = cv2.VideoCapture(0)
        frame_width, frame_height = 1280, 720

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(self.video_file, fourcc, 20.0, (frame_width, frame_height))

        while cap.isOpened() and self.is_running:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture video")
                break

            frame = cv2.resize(frame, (frame_width, frame_height))
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Pose detection
            results = self.pose.process(image)
            # Hand detection
            hand_results = self.hands.process(image)

            if results.pose_landmarks:
                # Draw pose landmarks on the image
                mp.solutions.drawing_utils.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                self.extract_pose_keypoints(results.pose_landmarks.landmark)

            if hand_results.multi_hand_landmarks:
                for hand_index, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                    # Determine if the hand is left or right
                    hand_label = hand_results.multi_handedness[hand_index].classification[0].label
                    hand_type = "left" if hand_label == "Left" else "right"

                    # Draw hand landmarks on image
                    mp.solutions.drawing_utils.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Call extract_hand_keypoints with the correct hand landmarks and hand type
                    self.extract_hand_keypoints(hand_landmarks, hand_type)

            # Write the frame to the output video file
            out.write(frame)

            # Display the frame
            cv2.imshow('Pose Estimation', frame)

            if cv2.waitKey(5) & 0xFF == 27:  # Press 'ESC' to exit
                break

            self.frame_counter += 1  # Increment the frame counter

        # Release resources
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        self.save_keypoints_data()  # Save keypoints data to a text file

    def extract_pose_keypoints(self, landmarks):
    # Define keypoint mappings for pose landmarks
        keypoint_map = {
            mp_pose.PoseLandmark.NOSE.value: "nose",
            mp_pose.PoseLandmark.LEFT_EYE.value: "left_eye",
            mp_pose.PoseLandmark.RIGHT_EYE.value: "right_eye",
            mp_pose.PoseLandmark.LEFT_EAR.value: "left_ear",
            mp_pose.PoseLandmark.RIGHT_EAR.value: "right_ear",
            mp_pose.PoseLandmark.LEFT_SHOULDER.value: "shoulder_left",
            mp_pose.PoseLandmark.RIGHT_SHOULDER.value: "shoulder_right",
            mp_pose.PoseLandmark.LEFT_ELBOW.value: "elbow_left",
            mp_pose.PoseLandmark.RIGHT_ELBOW.value: "elbow_right",
            mp_pose.PoseLandmark.LEFT_WRIST.value: "wrist_left",
            mp_pose.PoseLandmark.RIGHT_WRIST.value: "wrist_right",
            mp_pose.PoseLandmark.LEFT_HIP.value: "hip_left",
            mp_pose.PoseLandmark.RIGHT_HIP.value: "hip_right",
            mp_pose.PoseLandmark.LEFT_KNEE.value: "knee_left",
            mp_pose.PoseLandmark.RIGHT_KNEE.value: "knee_right",
            mp_pose.PoseLandmark.LEFT_ANKLE.value: "ankle_left",
            mp_pose.PoseLandmark.RIGHT_ANKLE.value: "ankle_right",
            mp_pose.PoseLandmark.LEFT_HEEL.value: "heel_left",
            mp_pose.PoseLandmark.RIGHT_HEEL.value: "heel_right",
            mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value: "foot_index_left",
            mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value: "foot_index_right"
        }
        

        # Only capture and store keypoints if detected and visible
        for idx, key in keypoint_map.items():
            # Check if the landmark index exists and meets the visibility threshold
            if idx < len(landmarks) and landmarks[idx].visibility > 0.5:
                landmark = landmarks[idx]
                self.keypoints_data[key].append([self.frame_counter, landmark.x, landmark.y, landmark.z]) 

    def extract_hand_keypoints(self, hand_landmarks, hand_type):
        # Define required landmarks with keys for both hands
        required_landmarks = {
            f"{hand_type}_index_finger_tip": mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP,
            f"{hand_type}_thumb_tip": mp.solutions.hands.HandLandmark.THUMB_TIP,
        }

        for keypoint, landmark in required_landmarks.items():
            # Check if landmark index exists
            if landmark < len(hand_landmarks.landmark):
                x, y, z = hand_landmarks.landmark[landmark].x, hand_landmarks.landmark[landmark].y, hand_landmarks.landmark[landmark].z
                self.keypoints_data[keypoint].append([self.frame_counter, x, y, z])

    def save_keypoints_data(self):
        # Save the keypoints data to a .txt file
        with open(self.keypoints_file, 'w') as f:
            for keypoint, positions in self.keypoints_data.items():
                if positions:
                    f.write(f"{keypoint}:\n")
                    for pos in positions:
                        f.write(f"  Frame {pos[0]}: x={pos[1]:.4f}, y={pos[2]:.4f}, z={pos[3]:.4f}\n")
                    f.write("\n")
        print(self.keypoints_file)
        
        # Append to the shared file if it exists, otherwise create and write
        mode = 'a' if os.path.exists("last_saved_filename.txt") else 'w'
        with open("last_saved_filename.txt", mode) as shared_file:
            shared_file.write(self.keypoints_file + '\n')
            
    def is_camera_available(self):
        cap = cv2.VideoCapture(0)  # Try to open the default camera (index 0)
        is_opened = cap.isOpened()  # Check if the camera is opened successfully
        cap.release()  # Release the camera
        return is_opened  # Return whether the camera is available
    
    def listen_for_stop_command(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            while self.is_running:
                try:
                    audio = recognizer.listen(source, timeout=5)
                    command = recognizer.recognize_google(audio).lower()
                    if "stop" in command:
                        self.is_running = False
                        break
                except sr.UnknownValueError:
                    continue
                except sr.WaitTimeoutError:
                    continue
                except sr.RequestError as e:
                    print(f"Error: {e}")
                    break

if __name__ == "__main__":
    # Start the video capture in Python
    pose_service = PoseEstimationService()

    # Start voice recognition in separate thread
    voice_thread = threading.Thread(target=pose_service.listen_for_stop_command)
    voice_thread.daemon = True
    voice_thread.start()

    # Check if camera is available before starting video capture
    if pose_service.is_camera_available():
        pose_service.start_video_capture()
    else:
        print("Camera not detected. Please connect a camera and try again.")

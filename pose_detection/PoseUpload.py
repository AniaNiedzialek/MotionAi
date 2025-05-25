import cv2
import mediapipe as mp
import numpy as np
import argparse
import os

# Initialize MediaPipe Pose and Hands
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

class PoseEstimationService:
    def __init__(self, video_path, video_type):
        self.pose = mp_pose.Pose()
        self.hands = mp_hands.Hands()
        self.keypoints_data = self.initialize_keypoints_data()
        self.frame_counter = 0
        self.video_path = video_path
        self.video_type = video_type.lower() # "beginner" or "pro"

         # Load existing file names to avoid conflicts
        self.existing_filenames = self.load_existing_filenames()

        # Set filenames based on video type
        self.keypoints_file = self.generate_filename(f"{self.video_type}.txt")
        self.video_file = self.generate_filename(f"{self.video_type}.avi")

    def load_existing_filenames(self):
        if os.path.exists("last_saved_filename.txt"):
            with open("last_saved_filename.txt", 'r') as f:
                return {line.strip() for line in f}  # Use a set for fast lookup
            
        return set()

    def generate_filename(self, base_filename):
        # Initialize base name and extension
        base_name, extension = os.path.splitext(base_filename)
        counter = 0

        # Check if the base name exists in existing filenames
        if base_filename not in self.existing_filenames and not os.path.exists(base_filename):
            return base_filename # Return base name if it doesn't exist
        
        # Increment filename if it already exists
        while True:
            counter += 1
            new_filename = f"{base_name}_{counter}{extension}" # Generate new file name

            if new_filename not in self.existing_filenames and not os.path.exists(new_filename):
                # Add the new filename to existing filenames set to avoid future conflicts
                self.existing_filenames.add(new_filename)
                return new_filename  # Return the first non-existing filename 
            
    def initialize_keypoints_data(self):
        return {
            "nose": [], "left_eye": [], "right_eye": [], "left_ear": [], "right_ear": [],
            "shoulder_left": [], "shoulder_right": [], "elbow_left": [], "elbow_right": [],
            "wrist_left": [], "wrist_right": [], "hip_left": [], "hip_right": [],
            "knee_left": [], "knee_right": [], "ankle_left": [], "ankle_right": [],
            "heel_left": [], "heel_right": [], "foot_index_left": [], "foot_index_right": [],
            "left_index_finger_tip": [], "right_index_finger_tip": [],
            "left_thumb_tip": [], "right_thumb_tip": []
        }

    def start_video_capture(self):
        cap = cv2.VideoCapture(self.video_path)

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Define the codec and create VideoWriter object for keypoints-only video
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(self.video_file, fourcc, 20.0, (frame_width, frame_height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("End of video or failed to read frame.")
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Pose detection
            pose_results = self.pose.process(image)
            # Hand detection
            hand_results = self.hands.process(image)

            if pose_results.pose_landmarks:
                # Draw pose landmarks on the image
                mp.solutions.drawing_utils.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                self.extract_pose_keypoints(pose_results.pose_landmarks.landmark)

            if hand_results.multi_hand_landmarks:
                for hand_index, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                    # Determine if the hand is left or right
                    hand_label = hand_results.multi_handedness[hand_index].classification[0].label
                    hand_type = "left" if hand_label == "Left" else "right"

                    # Draw hand landmarks on image
                    mp.solutions.drawing_utils.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Call extract_hand_keypoints with the correct hand landmarks and hand type
                    self.extract_hand_keypoints(hand_landmarks, hand_type)

            # Write the keypoints frame (frame) to the output video file
            out.write(frame)

            # Display the keypoints-only frame
            cv2.imshow('Keypoints Line Video', frame)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a video for pose estimation.")
    parser.add_argument('--video', dest='video_path', type=str, help='Path to the video file')
    parser.add_argument('--type', dest='video_type', type=str, help='Type of video ("beginner" or "pro")')
    args = parser.parse_args()

    pose_service = PoseEstimationService(args.video_path, args.video_type)
    pose_service.start_video_capture()


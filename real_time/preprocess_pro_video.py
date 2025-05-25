import cv2
import mediapipe as mp
import numpy as np
import json
import os

def extract_keypoints(video_path, output_json_path):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Cannot open video file {video_path}")
        return None

    all_frames_data = []
    frame_index = 0

    print(f"Processing video: {video_path}")
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break # End of video

        # Convert the BGR image to RGB.
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # Process the image and find pose landmarks.
        results = pose.process(image_rgb)

        frame_keypoints = {}
        if results.pose_landmarks:
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                landmark_name = mp_pose.PoseLandmark(idx).name
                # Store x, y, z, visibility
                frame_keypoints[landmark_name] = [landmark.x, landmark.y, landmark.z, landmark.visibility]

        all_frames_data.append({"frame_index": frame_index, "keypoints": frame_keypoints})
        frame_index += 1

        if frame_index % 100 == 0:
            print(f"Processed {frame_index} frames...")

    cap.release()
    pose.close()
    print(f"Finished processing. Total frames: {frame_index}")

    # Save to JSON
    try:
        with open(output_json_path, 'w') as f:
            json.dump(all_frames_data, f, indent=4)
        print(f"Keypoints saved to {output_json_path}")
        return all_frames_data
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return None

if __name__ == "__main__":
    pro_video = "pro.avi" 
    output_file = "professional_keypoints.json"
    if not os.path.exists(pro_video):
         print(f"Error: Professional video not found at {pro_video}")
    else:
        extract_keypoints(pro_video, output_file)
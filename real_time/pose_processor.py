import mediapipe as mp
import numpy as np
import cv2

class PoseProcessor:
    """Handles pose detection and analysis using MediaPipe"""
    
    def __init__(self, min_detection_confidence=0.6, min_tracking_confidence=0.6):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
    def extract_keypoints(self, frame):
        """Process a frame and extract pose keypoints"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.pose.process(frame_rgb)
        
        keypoints = {}
        if results.pose_landmarks:
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                landmark_name = self.mp_pose.PoseLandmark(idx).name
                keypoints[landmark_name] = [landmark.x, landmark.y, landmark.z, landmark.visibility]
                
        return keypoints, results
        
    def draw_pose(self, frame, results):
        """Draw pose landmarks on the frame"""
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
            )
        return frame
        
    def draw_professional_pose(self, frame, pro_kpts, deviations, frame_width, frame_height):
        """Draw professional pose landmarks with highlighting for deviations"""
        if not pro_kpts:
            return frame
            
        highlight_color = (0, 0, 255)  # Red for highlighting deviations (BGR)
        normal_point_color = (0, 255, 0)  # Green for normal points (BGR)
        normal_line_color = (150, 255, 150)  # Light Green for normal lines (BGR)
        
        # Dictionary to store pixel coordinates for drawing
        pro_pixel_coords = {}
        
        # Draw points
        for joint_name, pro_coord in pro_kpts.items():
            if pro_coord:  # Check if data exists for this joint
                # Convert normalized coords to pixel coords
                px = int(pro_coord[0] * frame_width)
                py = int(pro_coord[1] * frame_height)
                pro_pixel_coords[joint_name] = (px, py)
                
                # Determine color based on deviation
                point_color = highlight_color if joint_name in deviations else normal_point_color
                cv2.circle(frame, (px, py), radius=4, color=point_color, thickness=-1)
                
        # Draw connections
        for connection in self.mp_pose.POSE_CONNECTIONS:
            try:
                # Handle different connection formats
                if isinstance(connection[0], int) and isinstance(connection[1], int):
                    start_landmark = self.mp_pose.PoseLandmark(connection[0])
                    end_landmark = self.mp_pose.PoseLandmark(connection[1])
                else:
                    start_landmark = connection[0]
                    end_landmark = connection[1]
                    
                start_joint_name = start_landmark.name
                end_joint_name = end_landmark.name
                
                # Check if both connected joints were found and drawn
                if start_joint_name in pro_pixel_coords and end_joint_name in pro_pixel_coords:
                    start_pt = pro_pixel_coords[start_joint_name]
                    end_pt = pro_pixel_coords[end_joint_name]
                    
                    # Determine color based on deviation
                    line_color = highlight_color if (start_joint_name in deviations or 
                                                    end_joint_name in deviations) else normal_line_color
                    cv2.line(frame, start_pt, end_pt, line_color, thickness=2)
                    
            except Exception as e:
                print(f"Error processing connection {connection}: {e}")
                continue
                
        return frame
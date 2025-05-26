from database import MotionDatabase

class MotionPlayer:
    """Manages professional motion playback and frame selection"""
    
    def __init__(self, db=None):
        self.db = db or MotionDatabase()
        self.professional_keypoints = []
        self.current_motion_id = None
        self.current_frame_index = 0
        self.advance_score_threshold = 98.0  # Score needed to move to next pose
        
    def load_motion(self, motion_id=None):
        """Load keypoints from database by motion ID or get first available"""
        try:
            if motion_id is None:
                motions = self.db.get_motions_list()
                if not motions:
                    print("No motions found in database!")
                    return False
                motion_id = motions[0]["id"]
                
            keypoints_data = self.db.get_motion(motion_id)
            
            if keypoints_data:
                self.professional_keypoints = keypoints_data
                self.current_motion_id = motion_id
                self.current_frame_index = 0
                print(f"Loaded {len(self.professional_keypoints)} frames from database (Motion ID: {motion_id}).")
                return True
            else:
                print(f"No keypoints found for motion ID {motion_id}")
                return False
                
        except Exception as e:
            print(f"Error loading keypoints: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def get_current_frame_keypoints(self):
        """Get keypoints for the current frame"""
        if not self.professional_keypoints:
            return None
            
        if self.current_frame_index >= len(self.professional_keypoints):
            self.current_frame_index = self.current_frame_index % len(self.professional_keypoints)
            
        frame_data = self.professional_keypoints[self.current_frame_index]
        
        if "keypoints" in frame_data:
            return frame_data["keypoints"]
        else:
            print(f"Warning: Frame {self.current_frame_index} in professional data has unexpected format.")
            return None
            
    def check_advance_frame(self, score):
        """Check if we should advance to the next frame based on score"""
        if score >= self.advance_score_threshold:
            print(f"DEBUG: Pose {self.current_frame_index + 1} matched! Score: {score:.1f}. Advancing.")
            self.current_frame_index += 1
            if self.current_frame_index >= len(self.professional_keypoints):
                self.current_frame_index = 0
            return True
        return False
        
    def get_frame_count(self):
        """Get total number of frames in the current motion"""
        return len(self.professional_keypoints)
        
    def get_display_frame_number(self):
        """Get the 1-based frame number for display purposes"""
        if not self.professional_keypoints:
            return 0
        return self.current_frame_index + 1
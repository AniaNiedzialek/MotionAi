import numpy as np

class MotionComparer:
    """Compares user and professional poses and provides feedback"""
    
    def __init__(self, deviation_threshold=0.35):
        self.deviation_threshold = deviation_threshold
        
    def calculate_similarity(self, user_kpts, pro_kpts):
        """Calculate similarity between user and professional keypoints"""
        if not user_kpts or not pro_kpts:
            return 0.0, "No pose detected", set()
            
        total_distance = 0
        common_joints = 0
        max_possible_dist_per_joint = np.sqrt(1**2 + 1**2 + 1**2)
        
        feedback_details = []
        deviating_joints = set()
        
        for joint_name, user_coord in user_kpts.items():
            if joint_name in pro_kpts and pro_kpts[joint_name]:
                pro_coord = pro_kpts[joint_name]
                dist = np.linalg.norm(np.array(user_coord[:3]) - np.array(pro_coord[:3]))
                total_distance += dist
                common_joints += 1
                
                # Check for significant deviation
                if dist > self.deviation_threshold:
                    joint_title = joint_name.replace('_', ' ').title()
                    feedback_details.append(f"Check {joint_title}")
                    deviating_joints.add(joint_name)
                    
        if common_joints == 0:
            return 0.0, "Cannot compare poses", set()
            
        avg_distance = total_distance / common_joints
        normalized_distance = avg_distance / max_possible_dist_per_joint
        score = max(0.0, 100.0 * (1.0 - normalized_distance))
        
        if not feedback_details:
            feedback = "Good alignment!" if score > 85 else "Keep practicing alignment."
        else:
            feedback = "Corrections needed: " + ", ".join(feedback_details[:2])
            
        return score, feedback, deviating_joints
import json
from database import MotionDatabase

def migrate_json_to_db():
    """Migrate motion data from JSON files to the SQLite database."""
    
    # Path to existing JSON
    json_file = "./real_time/professional_keypoints.json"
    
    try:
        # Load existing JSON data
        with open(json_file, 'r') as file:
            keypoints_data = json.load(file)
        
        # Initialize the database    
        db = MotionDatabase()
        
        # Add to database 
        motion_id = db.add_motion(
            name="Professional Keypoints",
            category="dance",
            keypoints_data=keypoints_data
        )
        
        if motion_id:
            print(f"Successfully migrated motion with ID: {motion_id}")
            return motion_id
        else:
            print("Failed to migrate motion data.")
            return None
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return None
    
if __name__ == "__main__":
    migrate_json_to_db()
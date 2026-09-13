import json
import os

from database import MotionDatabase

# Resolve the bundled keypoints next to this module so the script works from any directory.
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON_PATH = os.path.join(MODULE_DIR, "professional_keypoints.json")
DEFAULT_MOTION_NAME = "Professional Keypoints"


def migrate_json_to_db(db=None, json_file=DEFAULT_JSON_PATH, name=DEFAULT_MOTION_NAME):
    """Migrate motion data from the bundled JSON file into the SQLite database.

    Returns the motion id, or None if nothing was migrated. Safe to run more than
    once: a motion with the same name is not inserted a second time.
    """
    try:
        db = db or MotionDatabase()

        # Skip if the motion is already stored, so repeat runs do not duplicate it.
        existing = next((m for m in db.get_motions_list() if m["name"] == name), None)
        if existing:
            print(f"Motion '{name}' already present with ID: {existing['id']}. Nothing to do.")
            return existing["id"]

        if not os.path.exists(json_file):
            print(f"Keypoints file not found: {json_file}")
            return None

        with open(json_file, 'r') as file:
            keypoints_data = json.load(file)

        if not keypoints_data:
            print(f"No keypoints found in {json_file}.")
            return None

        motion_id = db.add_motion(
            name=name,
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

import sqlite3
import json
import os
from typing import Dict, List, Optional, Any

# Resolve the database next to this module so the app works from any directory.
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(MODULE_DIR, "motion_data.db")


class MotionDatabase:
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the SQLite database for motion storage."""
        self.db_path = db_path or DEFAULT_DB_PATH
        self._create_tables()

    # --------------------------------------------------------------------------
    # Schema setup
    # --------------------------------------------------------------------------
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Categories table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
            """
        )

        # Motions table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS motions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
            """
        )

        # Frames table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY,
                motion_id INTEGER,
                frame_index INTEGER,
                frame_data TEXT,
                FOREIGN KEY (motion_id) REFERENCES motions (id)
            )
            """
        )

        conn.commit()
        conn.close()

    # --------------------------------------------------------------------------
    # Insert operations
    # --------------------------------------------------------------------------
    def add_motion(self, name: str, category: str, keypoints_data: List[Dict[str, Any]]) -> Optional[int]:
        """Add a new motion sequence (and its frames) to the database."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            # Ensure category exists
            cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,))
            cur.execute("SELECT id FROM categories WHERE name = ?", (category,))
            category_id = cur.fetchone()[0]

            # Insert motion
            cur.execute(
                "INSERT INTO motions (name, category_id) VALUES (?, ?)",
                (name, category_id),
            )
            motion_id = cur.lastrowid

            # Insert each frame
            for i, frame_data in enumerate(keypoints_data):
                cur.execute(
                    "INSERT INTO frames (motion_id, frame_index, frame_data) VALUES (?, ?, ?)",
                    (motion_id, i, json.dumps(frame_data)),
                )

            conn.commit()
            print(f"Motion '{name}' added with ID {motion_id}.")
            return motion_id

        except Exception as e:
            conn.rollback()
            print(f"Error adding motion: {e}")
            return None
        finally:
            conn.close()

    # --------------------------------------------------------------------------
    # Retrieval
    # --------------------------------------------------------------------------
    def get_motion(self, motion_id: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve all frames for a specific motion ID."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT frame_data FROM frames
                WHERE motion_id = ?
                ORDER BY frame_index
                """,
                (motion_id,),
            )
            rows = cur.fetchall()
            frames = [json.loads(row[0]) for row in rows if row and row[0]]
            return frames if frames else None
        except Exception as e:
            print(f"Error loading keypoints: {e}")
            return None
        finally:
            conn.close()

    def get_motion_by_name(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve motion frames by motion name."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM motions WHERE name = ?", (name,))
            row = cur.fetchone()
            if not row:
                print(f"No motion found with name '{name}'.")
                return None
            return self.get_motion(row[0])
        finally:
            conn.close()

    def get_motions_list(self) -> List[Dict[str, Any]]:
        """Return list of all motions with frame counts."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT 
                    m.id,
                    m.name,
                    COALESCE(c.name, 'Uncategorized') AS category,
                    COUNT(f.id) AS frame_count
                FROM motions m
                LEFT JOIN categories c ON m.category_id = c.id
                LEFT JOIN frames f ON f.motion_id = m.id
                GROUP BY m.id
                ORDER BY m.created_at DESC
                """
            )
            motions = []
            for motion_id, name, category, frame_count in cur.fetchall():
                motions.append(
                    {
                        "id": motion_id,
                        "name": name,
                        "category": category,
                        "frame_count": frame_count,
                    }
                )
            return motions
        finally:
            conn.close()

    def get_categories(self) -> List[str]:
        """Return all category names."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM categories ORDER BY name")
            return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

    # --------------------------------------------------------------------------
    # Deletion
    # --------------------------------------------------------------------------
    def delete_motion(self, motion_id: int) -> bool:
        """Delete a motion and all its frames."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM frames WHERE motion_id = ?", (motion_id,))
            cur.execute("DELETE FROM motions WHERE id = ?", (motion_id,))
            conn.commit()
            print(f"Motion with ID {motion_id} deleted.")
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting motion: {e}")
            return False
        finally:
            conn.close()

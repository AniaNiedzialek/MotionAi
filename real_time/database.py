import sqlite3
import json
import os
from typing import Dict, List, Any, Optional

class MotionDatabase:
    def __init__(self, db_path="./real_time/motion_data.db"):
        """Initialize the SQLite database for motion storage"""
        
        self.db_path = db_path
        self._create_tables()
        
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )            
        ''')
        
        # Create motions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS motions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )            
        ''')
        
        # Create frames table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY,
                motion_id INTEGER,
                frame_index INTEGER,
                frame_data TEXT,
                FOREIGN KEY (motion_id) REFERENCES motions (id)
            )            
        ''')
        
        conn.commit()
        conn.close()
    
    def add_motion(self, name: str, category: str, keypoints_data: List[Dict]) -> int:
        """Add a new motion sequence to the database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (category,)
            )
            
            # Get category ID
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            category_id = cursor.fetchone()[0]
            
            # Insert motion record
            cursor.execute(
                "INSERT INTO motions (name, category_id) VALUES (?, ?)",
                (name, category_id)
            )
            motion_id = cursor.lastrowid
            
            # Insert each frame
            for i, frame_data in enumerate(keypoints_data):
                cursor.execute(
                    "INSERT INTO frames (motion_id, frame_index, frame_data) VALUES (?, ?, ?)",
                    (motion_id, i, json.dumps(frame_data))
                )
            
            conn.commit()
            print(f"Motion '{name}' added with ID {motion_id}.")
            return motion_id
        
        except Exception as e:
            print(f"Error adding motion: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
            
    def get_motion(self, motion_id: int) -> Optional[List[Dict]]:
        """Get motion frame data by motion ID"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT frame_data FROM frames
                WHERE motion_id = ?
                ORDER BY frame_index               
            """)
            
            frames = []
            for (frame_data,) in cursor.fetchall():
                frames.append(json.loads(frame_data))
            
            return frames if frames else None
        
        finally:
            conn.close()
            
    def get_motion_by_name(self, name: str) -> Optional[List[Dict]]:
        """Get motion frame data by name"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            #Find motion ID by name
            cursor.execute("SELECT id FROM motions WHERE name = ?", (name,))
            result = cursor.fetchone()
            
            if not result:
                print(f"No motion found with name '{name}'.")
                return None
            
            motion_id = result[0]
            return self.get_motion(motion_id)
        
        finally:
            conn.close()
            
    def get_motions_list(self) -> List[Dict]:
        """Get list of all available motions"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT m.id, m.name, c.name, COUNT(f.id)
                FROM motions m
                JOIN categories c ON m.category_id = c.id
                LEFT JOIN frames f ON f.motion_id = m.id
                GROUP BY m.id    
            """)
            
            motions = []
            for motion_id, name, category, frame_count in cursor.fetchall():
                motions.append({
                    "id": motion_id,
                    "name": name,
                    "category": category,
                    "frame_count": frame_count
                })
                
            return motions
        finally:
            conn.close()
            
    
    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name FROM categories ORDER BY name")
            return [row[0] for row in cursor.fetchall()]
        
        finally:
            conn.close()
            
    def delete_motion(self, motion_id: int) -> bool:
        """Delete a motion and all its frames"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete frames first to maintain foreign key integrity
            cursor.execute("DELETE FROM frames WHERE motion_id = ?", (motion_id,))
            
            # Delete the motion record
            cursor.execute("DELETE FROM motions WHERE id = ?", (motion_id,))
            
            if cursor.rowcount == 0:
                conn.rollback()
                return False          
            
            conn.commit()
            print(f"Motion with ID {motion_id} deleted.")
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting motion: {e}")
            return False
        finally:
            conn.close()
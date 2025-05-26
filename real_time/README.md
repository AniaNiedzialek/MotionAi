- **`app.py`**: Main application entry point. Sets up the UI and orchestrates the interaction between all components.

- **`camera_manager.py`**: Handles camera initialization, frame capture, and resource management with proper cleanup.

- **`pose_processor.py`**: Processes video frames to extract human pose data using MediaPipe. Handles landmark detection and visualization.

- **`motion_comparer.py`**: Compares user poses with professional reference poses. Calculates similarity scores and generates feedback.

- **`motion_player.py`**: Manages playback of professional motion sequences based on user performance.

- **`database.py`**: Provides database operations for storing and retrieving motion data.

- **`motion_manager.py`**: Contains the MotionSelectionDialog for choosing pre-recorded motion sequences.

- **`motion_upload.py`**: Implements the MotionUploadDialog for adding new motion sequences to the system.

- **`migration.py`**: Database schema migration script to handle database upgrades.

- **`preprocess_pro_video.py`**: Utility for pre-processing professional videos into keypoint data.
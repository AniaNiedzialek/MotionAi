# Motion AI
**Enhancing Dance Skills with Real-Time Feedback**

## Overview
Motion AI helps users improve their dance skills by analyzing body movements and providing
feedback. Using **MediaPipe**, we capture key body points from a user and compare them to a
reference performance, addressing challenges like unmatched video lengths, varying data points,
and body size differences.

The repository contains two separate implementations that share the idea but not the code:

| Path | What it is | Comparison method |
| --- | --- | --- |
| `real_time/` | Python desktop app, live webcam feedback. This is the app you run. | Per-frame Euclidean distance between MediaPipe keypoints |
| `src/main/java/` | JavaFX offline analyzer, compares two recorded videos | Dynamic Time Warping over torso-normalized keypoints |

`pose_detection/`, `motion_database/` and `web_call/` hold Python scripts and sample data the
Java app shells out to via `ProcessBuilder`. They are not used by the Python app, but they are
not dead code either, so do not delete them while the Java analyzer is in use.

---

## Python real-time app (`real_time/`)

### Prerequisites
- Python 3.8 or later (developed on 3.11)
- A webcam

### Install
```bash
git clone https://github.com/AniaNiedzialek/MotionAi
cd MotionAi
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Install from `requirements.txt` rather than by hand. The versions there are pinned for a reason:
`real_time/pose_processor.py` uses the legacy `mp.solutions` API, which mediapipe removed after
0.10.21, so a plain `pip install mediapipe` produces a build the app cannot start against.

### Run
```bash
python real_time/app.py
```

On first launch the app seeds its SQLite database (`real_time/motion_data.db`) from the bundled
`real_time/professional_keypoints.json`, so "Load Motion" has a reference motion available
immediately. To seed it by hand instead:

```bash
python real_time/migration.py
```

Both the database and the bundled keypoints are resolved relative to `real_time/`, so the app can
be launched from any working directory.

### Using it
1. **Load Motion** picks a reference motion from the database.
2. **Start Practice** opens the webcam and begins scoring your pose against the current reference
   frame. The reference pose is drawn over the video feed in green.
3. **Add New Motion** records a new reference motion from your webcam or from a video file.
   Uploads support a target FPS, a detection confidence threshold, and linear interpolation of
   missing poses.

The reference sequence advances to the next frame once your score passes the threshold, so the
session is paced by how well you match rather than by wall-clock time.

### How the comparison works
For each processed frame the app extracts MediaPipe keypoints, then averages the Euclidean
distance between your joints and the reference joints. The average is scaled into a 0-100 score,
and any joint further away than the deviation threshold is called out in the feedback line.

This is a deliberately simple per-frame comparison. It does **not** normalize for body size or
camera distance, so stand roughly where the reference performer stood for meaningful scores.

### Layout
See `real_time/README.md` for a per-module description.

### Tests
```bash
pip install pytest
python -m pytest
```
The suite covers score calculation and database seeding. It does not need a camera or a display,
so it also runs on every push and pull request via `.github/workflows/tests.yml`.

### Troubleshooting

**"Status: Error: Could not open camera ..." on macOS.** The camera permission belongs to the
program that launched Python, not to Python itself. Grant it under
System Settings > Privacy & Security > Camera, ticking whichever terminal you used (Terminal,
iTerm, or VS Code), then restart that terminal. The permission prompt only appears the first time
the app tries to open the camera, which is when you press Start Practice.

**"module 'mediapipe' has no attribute 'solutions'".** A newer mediapipe is installed. Reinstall
the pinned version:
```bash
pip install -r requirements.txt --force-reinstall
```

**"Load Motion" shows an empty list.** The database is missing or empty. Delete it and let the app
reseed on the next launch:
```bash
rm -f real_time/motion_data.db
```

---

## Java analyzer (`src/main/java/`)

A separate JavaFX application that compares two recorded videos offline. It is where the
algorithm work described below lives.

### Prerequisites
- Java 21 or later (`pom.xml` compiles to 21)
- Maven 3.6 or later

### Run
```bash
mvn clean javafx:run
```

### Methodology

#### 1. MediaPipe Integration
MediaPipe provides robust detection of 33 key body points in 3D space (x, y, z) for each frame,
tracking shoulders, hips, elbows, and knees.

#### 2. Dynamic Time Warping (DTW)
DTW aligns sequences of body movements from users and professionals, so two performances of
different speed or length can still be compared.
- **Input Data**: keypoints stored in maps with frame numbers as keys and coordinates as values.
- **Sorting**: Merge Sort organizes frames for comparison. Small sublists are handled with
  Insertion Sort for efficiency.
- **Distance Calculation**: DTW quantifies movement differences for each body part.

#### 3. Normalization
Addresses body size differences to allow fair comparisons.
- **Torso Length Calculation**: uses shoulder and hip keypoints to derive a scale.
- **Scaling Key Points**: adjusts coordinates (x, y, z) relative to torso size.
- **Importance**: keeps comparisons consistent regardless of body size or distance from camera.

#### 4. Linear Interpolation
Fills gaps in keypoint data caused by motion blur or occlusion. If a keypoint is missing at
frame 6, it is estimated from the known keypoints at frames 5 and 7.

#### 5. Moving Average
Averages keypoint values over a time window to smooth out tracking noise, for example erratic
hand positions.

### Sorting Techniques
1. **Merge Sort**
   - Optimized through parallel processing.
   - Uses in-place sorting to minimize memory usage, especially for large datasets.
   - For sublists larger than 20 frames, recursive splitting with parallel execution keeps
     sorting fast.
2. **Insertion Sort**
   - Handles sublists below 20 frames, minimizing overhead compared to Merge Sort.

---

## Roadmap / Ideas
- Port torso normalization from the Java analyzer into the Python comparer, so scores stop
  depending on where the user stands.
- Add gesture detection.
- Track specific joints over time.
- Apply ML classification to movement patterns.

## Contributors
- Nguyen Pham
- Ania Niedzialek

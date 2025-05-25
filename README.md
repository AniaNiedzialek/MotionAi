# Motion AI  
**Enhancing Dance Skills with Real-Time Feedback**  

## Overview  
Motion AI is a project designed to help users improve their dance skills by analyzing their body movements and providing real-time feedback. Using advanced computer vision techniques with **MediaPipe**, we capture key body points from users and compare them to professional dancers, addressing challenges like unmatched video lengths, varying data points, and body size differences. Our solution involves a combination of algorithms to ensure smooth, accurate, and reliable data processing.  

## Key Features  
- **MediaPipe Integration**: Utilizes MediaPipe’s state-of-the-art pose estimation for efficient and accurate keypoint detection.  
- **Dynamic Time Warping (DTW)**: Measures similarity between sequences with varying time/speed, aligning user and professional movements.  
- **Normalization**: Scales body points relative to torso length, enabling consistent pose comparison across different body sizes.  
- **Linear Interpolation**: Fills gaps in key point data caused by detection issues like motion blur or occlusions.  
- **Moving Average**: Smooth data fluctuations, filtering noise for improved accuracy in analysis.  

## Installation

### 1. **Prerequisites**
- **Python 3.8 or later**
- **Java 23 or later**
- **Maven 3.6 or later**

### 2. **Clone the Repository**
```bash
git clone https://github.com/nmhp16/motion_ai
cd motion_ai
```
### 3. **Required Python Packages**
```bash
pip install opencv-python mediapipe SpeechRecognition pyaudio
```

**Optional**
```bash
pip install numpy matplotlib
```

### 4. **Running Project**
```bash
mvn javafx:run
```
## Methodology  

### 1. **MediaPipe Integration**  
MediaPipe is the core of our pose estimation pipeline, providing robust, real-time detection of 33 key body points in 3D space (x, y, z) for each frame of the video.  
- **Pose Detection**: Tracks keypoints such as shoulders, hips, elbows, and knees, ensuring accurate representation of user movements.  
- **Advantages**:  
  - Real-time processing for seamless feedback.  
  - High precision even in challenging scenarios like partial occlusions or complex poses.  

### 2. **Dynamic Time Warping (DTW)**  
DTW aligns sequences of body movements from users and professionals for accurate comparisons.  
- **Input Data**: Body keypoints detected by MediaPipe are stored in maps with frame numbers as keys and coordinates as values.  
- **Sorting**: Merge Sort organizes frames for comparison. Small sublists are handled with Insertion Sort for efficiency.  
- **Distance Calculation**: DTW quantifies movement differences for each body part.  

### 3. **Normalization**  
Addresses body size differences to allow fair comparisons.  
- **Torso Length Calculation**: Uses keypoints like shoulders and hips detected by MediaPipe to scale body data.  
- **Scaling Key Points**: Adjusts coordinates (x, y, z) relative to torso size.  
- **Importance**: Ensures data consistency for accurate pose comparisons, regardless of body size differences.  

### 4. **Linear Interpolation**  
Fills gaps in keypoint data to ensure complete movement sequences.  
- **Concept**: Estimates missing values between detected points using a straight-line assumption.  
- **Example**: If a keypoint is missing at frame 6, it is estimated using the known keypoints at frames 5 and 7.  

### 5. **Moving Average**  
Smooth data fluctuations and filter out noise for improved accuracy.  
- **Concept**: Averages keypoint values over a specific time window to eliminate short-term variations.  
- **Example**: Reduces erratic hand movement data caused by tracking inaccuracies, creating a smoother trajectory.  

## Implementation Details  

### Sorting Techniques  
1. **Merge Sort**
   - Optimize performance through parallel processing.
   - Utilizes in-place sorting to minimize memory usage and improve efficiency, especially for large datasets.
   - For sublists larger than 20 frames, recursive splitting combined with parallel execution ensures faster and more efficient sorting.
 

2. **Insertion Sort**  
   - Handles smaller sublists (below 20 frames) for efficiency, minimizing overhead compared to Merge Sort.  

### Data Processing Algorithms  
- **Normalization** ensures scalability across different body types by using torso length as a reference for consistent comparisons.  
- **Linear Interpolation** fills missing keypoints, maintaining data integrity even with incomplete frame data.  
- **Moving Average** smooths detected keypoints to reduce noise and highlight significant trends.  
 
## Contributors

- Aron Mundanilkunathil
- Huu Tinh Nguyen
- Jay Barrios Abarquez
- Kundyz Serzhankyzy
- Uyen Pham
- Ryan Nguyen
- Ania Niedzialek
- Mohammed Nassar
- Sunny Doan
- Nguyen Pham
  



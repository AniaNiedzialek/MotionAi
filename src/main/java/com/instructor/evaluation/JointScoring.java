package com.instructor.evaluation;

import java.util.Map;

import com.instructor.algorithms.DynamicTimeWarping;

public class JointScoring {
    private static final float THRESHOLD = 0.2f;
    private static final float DTW_THRESHOLD = 0.05f;

    // Function to get feedback for joint movement
    public static String getJointFeedback(String jointName, float[] userFrameData, float[] proFrameData) {
        StringBuilder feedback = new StringBuilder();

        feedback.append("Frame feedback for ").append(jointName).append(": ");

        // Check X, Y, and Z directions and provide feedback
        if (userFrameData[0] > proFrameData[0] + THRESHOLD) {
            feedback.append("Move ").append(jointName).append(" to the left. ");
        } else if (userFrameData[0] < proFrameData[0] - THRESHOLD) {
            feedback.append("Move ").append(jointName).append(" to the right. ");
        }

        if (userFrameData[1] > proFrameData[1] + THRESHOLD) {
            feedback.append("Move ").append(jointName).append(" down. ");
        } else if (userFrameData[1] < proFrameData[1] - THRESHOLD) {
            feedback.append("Move ").append(jointName).append(" up. ");
        }

        if (userFrameData[2] > proFrameData[2] + THRESHOLD) {
            feedback.append("Move ").append(jointName).append(" back. ");
        } else if (userFrameData[2] < proFrameData[2] - THRESHOLD) {
            feedback.append("Move ").append(jointName).append(" forward. ");
        }

        feedback.append("\n");
        return feedback.toString();
    }

    // Function to compare user and pro frames, calculate DTW, and provide feedback
    public static String compareFramesAndProvideFeedback(String jointName, float[] userFrameData,
            float[] proFrameData) {
        // Calculate DTW distance (simulated for this example)
        float dtwDistance = DynamicTimeWarping.dtw(Map.of(0, userFrameData), Map.of(0, proFrameData));

        // If DTW distance is within the threshold, provide feedback
        if (dtwDistance <= DTW_THRESHOLD) {
            return getJointFeedback(jointName, userFrameData, proFrameData);
        } else {
            return "Pose is sufficiently aligned for " + jointName + " in this frame.\n";
        }
    }

    public static void generateFeedbackForAllJoints(Map<String, Map<Integer, float[]>> userDatabase,
            Map<String, Map<Integer, float[]>> proDatabase) {
        // Iterate through each joint in the user's database
        for (Map.Entry<String, Map<Integer, float[]>> entry : userDatabase.entrySet()) {
            String jointName = entry.getKey();
            Map<Integer, float[]> userFrames = entry.getValue();

            // Get corresponding pro frames for the joint
            Map<Integer, float[]> proFrames = proDatabase.get(jointName);

            if (proFrames != null) {
                // For each frame in the user's data, compare it with the corresponding pro
                // frame
                for (Map.Entry<Integer, float[]> frameEntry : userFrames.entrySet()) {
                    Integer frameIndex = frameEntry.getKey();
                    float[] userFrameData = frameEntry.getValue();
                    float[] proFrameData = proFrames.get(frameIndex);

                    // If there's no corresponding pro frame for this index, skip
                    if (proFrameData == null) {
                        continue;
                    }

                    // Get the feedback for the joint and frame
                    String feedback = compareFramesAndProvideFeedback(jointName, userFrameData, proFrameData);

                    // Print the feedback (or store it as required)
                    System.out.println("Feedback for joint: " + jointName + ", Frame: " + frameIndex);
                    System.out.println(feedback);
                }
            } else {
                System.out.println("No pro data found for joint: " + jointName);
            }
        }
    }

}

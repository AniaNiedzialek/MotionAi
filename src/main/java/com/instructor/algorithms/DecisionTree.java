package com.instructor.algorithms;

import java.util.Map;

public class DecisionTree {

    public DecisionTree() {
        // No need for a decision tree instance since we're comparing

        //classifying as hard, easy, or difficult 
        // 
    }

    /**
     * Compares the user's keypoints data with the professional keypoints data.
     * 
     * @param proKeypointsMap Professional keypoints data.
     * @param userKeypointsMap User keypoints data.
     * @return Similarity score indicating how similar the poses are.
     */
    public double comparePoses(Map<String, Map<Integer, float[]>> proKeypointsMap, 
                               Map<String, Map<Integer, float[]>> userKeypointsMap) {
        double totalDifference = 0.0;
        int frameCount = 0;

        // Assuming both maps have the same structure
        for (String keypoint : proKeypointsMap.keySet()) {
            Map<Integer, float[]> proFrames = proKeypointsMap.get(keypoint);
            Map<Integer, float[]> userFrames = userKeypointsMap.get(keypoint);

            for (Integer frame : proFrames.keySet()) {
                if (userFrames.containsKey(frame)) {
                    // Calculate distance between corresponding keypoints
                    float[] proKeypoint = proFrames.get(frame);
                    float[] userKeypoint = userFrames.get(frame);

                    double distance = calculateDistance(proKeypoint, userKeypoint);
                    totalDifference += distance;
                    frameCount++;
                }
            }
        }

        // Return average distance as a similarity score
        return frameCount > 0 ? totalDifference / frameCount : Double.MAX_VALUE; // Handle case with no frames
    }

    private double calculateDistance(float[] pointA, float[] pointB) {
        // Use Euclidean distance formula
        return Math.sqrt(Math.pow(pointA[0] - pointB[0], 2) + 
                         Math.pow(pointA[1] - pointB[1], 2) + 
                         Math.pow(pointA[2] - pointB[2], 2));
    }

    public String classifyPose(double similarityScore, double threshold) {
        return similarityScore < threshold ? "correct" : "incorrect";
    }
}

    
package com.instructor.algorithms;

import java.util.*;

import com.instructor.data.PoseDataProcessing;

public class DynamicTimeWarping {

    /**
     * Calculates the total Dynamic Time Warping (DTW) distance between two sets of
     * keypoints for all body parts.
     *
     * @param userKeypoints Map of user keypoints, with body parts as keys and
     *                      frames as values.
     * @param proKeypoints  Map of professional keypoints, with body parts as keys
     *                      and frames as values.
     * @return The total DTW distance between the two sets of keypoints.
     */
    public static float totalDtw(Map<String, Map<Integer, float[]>> userKeypoints,
            Map<String, Map<Integer, float[]>> proKeypoints) {
        float totalDtwDistance = 0;
        int partCount = 0;

        for (String keypoint : userKeypoints.keySet()) {

            // Check if the keypoint is needed
            if (isPartNeeded(keypoint)) {
                Map<Integer, float[]> userPartData = userKeypoints.getOrDefault(keypoint, new HashMap<>());
                Map<Integer, float[]> proPartData = proKeypoints.getOrDefault(keypoint, new HashMap<>());

                if (!userPartData.isEmpty() && !proPartData.isEmpty()) {
                    float dtwDistance = dtw(userPartData, proPartData);
                    totalDtwDistance += dtwDistance;
                    partCount++;
                }
            }
        }

        if (partCount > 0) {
            return totalDtwDistance / partCount;
        } else {
            return Float.MAX_VALUE;
        }
    }

    /**
     * Computes the Dynamic Time Warping (DTW) distance between two sets of keypoint
     * data.
     * 
     * This method calculates the DTW distance matrix and returns the normalized
     * cumulative distance between frames of user and professional keypoints.
     * 
     * @param userPartData A map of frame indices to keypoint coordinates for the
     *                     user.
     * @param proPartData  A map of frame indices to keypoint coordinates for the
     *                     professional.
     * @return The normalized DTW distance representing the similarity between the
     *         two datasets.
     */
    public static float dtw(Map<Integer, float[]> userPartData, Map<Integer, float[]> proPartData) {
        PoseDataProcessing poseDataProcessing = new PoseDataProcessing();

        // Use sorted keys to access data consistently
        List<Integer> userKeys = new ArrayList<>(userPartData.keySet());
        List<Integer> proKeys = new ArrayList<>(proPartData.keySet());
        MergeSort.mergeSort(userKeys, true); // Sort in ascending order
        MergeSort.mergeSort(proKeys, true); // Sort in ascending order

        int n = userKeys.size();
        int m = proKeys.size();

        float[][] dtwMatrix = new float[n + 1][m + 1];
        for (int i = 0; i <= n; i++) {
            Arrays.fill(dtwMatrix[i], Float.MAX_VALUE);
        }
        dtwMatrix[0][0] = 0;

        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= m; j++) {
                float[] userCoords = userPartData.get(userKeys.get(i - 1));
                float[] proCoords = proPartData.get(proKeys.get(j - 1));

                float cost = 0;
                if (userCoords != null && proCoords != null) {
                    cost = poseDataProcessing.calculateDistance(userCoords, proCoords);
                }

                dtwMatrix[i][j] = cost + Math.min(
                        Math.min(dtwMatrix[i - 1][j], dtwMatrix[i][j - 1]),
                        dtwMatrix[i - 1][j - 1]);
            }
        }

        return dtwMatrix[n][m] / Math.max(n, m);
    }

    /**
     * Calculates the Dynamic Time Warping (DTW) distance between two sets of
     * keypoints, as well as the alignment path that produces the minimum DTW
     * distance.
     * 
     * @param userPartData Map containing the keypoints data for the user, with
     *                     frames as keys and coordinates as values.
     * @param proPartData  Map containing the keypoints data for the professional
     *                     dancer, with frames as keys and coordinates as values.
     * @return A list of int[] arrays, where each array contains the frame numbers
     *         for the user and professional keypoints, respectively, that align
     *         together in the DTW path. The first element of the array is the
     *         user frame, and the second element is the professional frame.
     */
    public static List<int[]> dtwWithAlignmentPath(Map<Integer, float[]> userPartData,
            Map<Integer, float[]> proPartData) {
        PoseDataProcessing poseDataProcessing = new PoseDataProcessing();

        List<Integer> userKeys = new ArrayList<>(userPartData.keySet());
        List<Integer> proKeys = new ArrayList<>(proPartData.keySet());
        MergeSort.mergeSort(userKeys, true); // Sort in ascending order
        MergeSort.mergeSort(proKeys, true); // Sort in ascending order

        int n = userKeys.size();
        int m = proKeys.size();

        float[][] dtwMatrix = new float[n + 1][m + 1];
        int[][] pathMatrix = new int[n][m];

        for (int i = 0; i <= n; i++) {
            Arrays.fill(dtwMatrix[i], Float.MAX_VALUE);
        }
        dtwMatrix[0][0] = 0;

        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= m; j++) {
                float[] userCoords = userPartData.get(userKeys.get(i - 1));
                float[] proCoords = proPartData.get(proKeys.get(j - 1));

                float cost = 0;
                if (userCoords != null && proCoords != null) {
                    cost = poseDataProcessing.calculateDistance(userCoords, proCoords);
                }

                float minCost = Math.min(
                        Math.min(dtwMatrix[i - 1][j], dtwMatrix[i][j - 1]),
                        dtwMatrix[i - 1][j - 1]);
                dtwMatrix[i][j] = cost + minCost;

                if (minCost == dtwMatrix[i - 1][j]) {
                    pathMatrix[i - 1][j - 1] = 1; // Vertical
                } else if (minCost == dtwMatrix[i][j - 1]) {
                    pathMatrix[i - 1][j - 1] = 2; // Horizontal
                } else {
                    pathMatrix[i - 1][j - 1] = 3; // Diagonal
                }
            }
        }

        List<int[]> alignmentPath = new ArrayList<>();
        int i = n - 1, j = m - 1;

        while (i >= 0 && j >= 0) {
            alignmentPath.add(new int[] { userKeys.get(i), proKeys.get(j) });
            if (pathMatrix[i][j] == 1) {
                i--;
            } else if (pathMatrix[i][j] == 2) {
                j--;
            } else {
                i--;
                j--;
            }
        }

        Collections.reverse(alignmentPath);
        return alignmentPath;
    }

    /**
     * Helper method to check for only body parts needed
     * 
     * @param bodyPart Current body part
     * @return True if it is needed, False otherwise
     */
    private static boolean isPartNeeded(String bodyPart) {
        return bodyPart.equalsIgnoreCase("shoulder_left") || bodyPart.equalsIgnoreCase("shoulder_right")
                || bodyPart.equalsIgnoreCase("elbow_left") || bodyPart.equalsIgnoreCase("elbow_right")
                || bodyPart.equalsIgnoreCase("wrist_left") || bodyPart.equalsIgnoreCase("wrist_right")
                || bodyPart.equalsIgnoreCase("hip_left") || bodyPart.equalsIgnoreCase("hip_right")
                || bodyPart.equalsIgnoreCase("knee_left") || bodyPart.equalsIgnoreCase("knee_right")
                || bodyPart.equalsIgnoreCase("ankle_left") || bodyPart.equalsIgnoreCase("ankle_right")
                || bodyPart.equalsIgnoreCase("heel_left") || bodyPart.equalsIgnoreCase("heel_right")
                || bodyPart.equalsIgnoreCase("foot_index_left") || bodyPart.equalsIgnoreCase("foot_index_right")
                || bodyPart.equalsIgnoreCase("nose");
    }

}

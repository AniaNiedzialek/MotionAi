package com.instructor.evaluation;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.instructor.algorithms.DynamicTimeWarping;

public class PoseScoring {
	private PoseFeedback feedback = new PoseFeedback();
	private int score = 0;
	private int overallScore = 0;

	// Threshold for considering a pose as "wrong"
	private static final int THRESHOLD_SCORE = 70;

	/**
	 * Give score based on the similarity between User and Pro
	 * 
	 * @param similarityScore
	 * @param maxSimilarity
	 * @return
	 */
	public int calculateScore(float similarityScore, float maxSimilarity) {
		// Cap the similarity score to avoid exceeding maxSimilarity
		similarityScore = Math.min(similarityScore, maxSimilarity);

		// Normalize the similarity score on a scale of 0-1
		float normalizedSimilarity = similarityScore / maxSimilarity;

		// Calculate final score (out of 100) - lower normalized similarity gives higher
		// score
		return (int) Math.max(0, (1 - normalizedSimilarity) * 100);
	}

	/**
	 * Score user pose against professional pose and provide feedback
	 * 
	 * @param userKeypoints Map containing user keypoints
	 * @param proKeypoints  Map containing professional keypoints
	 */
	public void calculatePoseScore(Map<String, Map<Integer, float[]>> userKeypoints,
			Map<String, Map<Integer, float[]>> proKeypoints) {
		// Track frames where user performed poorly
		Map<String, List<Integer>> incorrectFrames = new HashMap<>();
		Map<String, List<Integer>> lowScoreFrames = new HashMap<>();

		for (String bodyPart : userKeypoints.keySet()) {
			Map<Integer, float[]> userPartData = userKeypoints.get(bodyPart);
			Map<Integer, float[]> proPartData = proKeypoints.get(bodyPart);

			// Check if there's user data and professional data for the body part
			if (userPartData == null || proPartData == null) {
				continue;
			}

			// Calculate DTW and obtain the alignment path
			List<int[]> alignmentPath = DynamicTimeWarping.dtwWithAlignmentPath(userPartData, proPartData);

			// Track overall score based on DTW distance
			float totalDtwDistance = 0;
			float maxDistance = 4.0f; // Replace actual value later

			for (int[] path : alignmentPath) {
				int userFrame = path[0];
				int proFrame = path[1];

				// Check for null values before creating the map
				float[] userFrameData = userPartData.get(userFrame);
				float[] proFrameData = proPartData.get(proFrame);

				// Skip this frame if either user or pro frame data is null
				if (userFrameData == null || proFrameData == null) {
					continue;
				}

				// Calculate the DTW distance for this pair of frames
				float frameDtwDistance = DynamicTimeWarping.dtw(
						Map.of(0, userPartData.get(userFrame)),
						Map.of(0, proPartData.get(proFrame)));

				totalDtwDistance += frameDtwDistance;
				score = calculateScore(frameDtwDistance, maxDistance);

				// Store low score frames
				if (score < THRESHOLD_SCORE) {

					// Track frames with poor alignment
					if (!incorrectFrames.containsKey(bodyPart)) {
						incorrectFrames.put(bodyPart, new ArrayList<>());
					}
					incorrectFrames.get(bodyPart).add(userFrame); // Add the frame number

					// Store the low score for this frame
					if (!lowScoreFrames.containsKey(bodyPart)) {
						lowScoreFrames.put(bodyPart, new ArrayList<>());
					}
					lowScoreFrames.get(bodyPart).add(score); // Add the low score
				}

			}

			// Calculate average DTW distance
			float averageDtwDistance = totalDtwDistance / alignmentPath.size();

			// Calculate overall score
			overallScore = calculateScore(averageDtwDistance, maxDistance);

			if (isPartNeeded(bodyPart)) {
				System.out.println("=================================================");
				System.out.println("Body Part: " + bodyPart);
				System.out.println("Overall Score: " + overallScore);

				// Provide feedback for the current frame
				System.out.println(feedback.provideSpecificFeedback(overallScore, bodyPart));
				System.out.println();

				// Check if there is bad score which < 90
				if (lowScoreFrames.get(bodyPart) == null || lowScoreFrames.get(bodyPart).isEmpty()) {
					System.out.println("Bad Scores: none");
					System.out.println();
				} else {
					System.out.println("Bad Scores: " + lowScoreFrames.get(bodyPart));
					System.out.println();
				}

				// Check for incorrect frames connect with bad score
				if (incorrectFrames.get(bodyPart) == null) {
					System.out.println("Incorrect frames: none.");
				} else {
					System.out.println("Incorrect frames: " + incorrectFrames.get(bodyPart));
				}

				System.out.println();
			}
		}
	}

	/**
	 * Method to check for only body parts needed
	 * 
	 * @param bodyPart Current body part
	 * @return True if it is needed, False otherwise
	 */
	public boolean isPartNeeded(String bodyPart) {
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

	/**
	 * Generates a comparison prompt with aligned frame information between user and
	 * pro keypoints.
	 *
	 * This method calculates the alignment path using Dynamic Time Warping (DTW)
	 * for each required
	 * body part and constructs a prompt string containing details of aligned
	 * frames.
	 *
	 * @param userKeypoints Map of user keypoints across frames, categorized by body
	 *                      parts.
	 * @param proKeypoints  Map of professional keypoints across frames, categorized
	 *                      by body parts.
	 * @return A formatted string containing the aligned frames and their respective
	 *         keypoint coordinates.
	 */
	public String generateComparisonPrompt(Map<String, Map<Integer, float[]>> userKeypoints,
			Map<String, Map<Integer, float[]>> proKeypoints, String partNeeded) {

		// Track alignment frames between user and pro keypoints
		Map<String, List<int[]>> alignmentFrames = new HashMap<>();

		StringBuilder prompt = new StringBuilder();

		for (String bodyPart : userKeypoints.keySet()) {
			if (!bodyPart.equalsIgnoreCase(partNeeded)) {
				continue;
			}

			Map<Integer, float[]> userPartData = userKeypoints.get(bodyPart);
			Map<Integer, float[]> proPartData = proKeypoints.get(bodyPart);

			// skip this body part if either user or pro part data is null
			if (proPartData == null || userPartData == null) {
				continue;
			}

			// Calculate alignment path using DTW
			List<int[]> alignmentPath = DynamicTimeWarping.dtwWithAlignmentPath(userPartData, proPartData);
			alignmentFrames.put(bodyPart, alignmentPath);

			// Iterate over the aligned frames to generate the comparison
			for (int[] path : alignmentPath) {
				int userFrame = path[0];
				int proFrame = path[1];

				float[] userFrameData = userPartData.get(userFrame);
				float[] proFrameData = proPartData.get(proFrame);

				if (userFrameData == null || proFrameData == null) {
					continue;
				}

				// Calculate the DTW distance and score for the current frame
				float frameDtwDistance = DynamicTimeWarping.dtw(
						Map.of(0, userPartData.get(userFrame)),
						Map.of(0, proPartData.get(proFrame)));
				int score = calculateScore(frameDtwDistance, 4.0f); // Max distance of 4.0f (adjust if needed)

				// Only append to the prompt if the score is below 80
				if (score < THRESHOLD_SCORE) {
					if (prompt.length() == 0) {
						prompt.append("Body Part: ").append(bodyPart).append("\n");
					}

					prompt.append(String.format("User Frame: %d", userFrame));
					prompt.append(String.format("  User: x=%.4f, y=%.4f, z=%.4f\n", userFrameData[0], userFrameData[1],
							userFrameData[2]));

					prompt.append(String.format("Pro Frame: %d\n", proFrame));
					prompt.append(String.format("  Pro:  x=%.4f, y=%.4f, z=%.4f\n\n", proFrameData[0], proFrameData[1],
							proFrameData[2]));
				}
			}
		}
		return prompt.toString();
	}
}

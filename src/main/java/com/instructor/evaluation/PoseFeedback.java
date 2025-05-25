package com.instructor.evaluation;

import java.util.Map;
import java.util.HashMap;

public class PoseFeedback {
    private Map<String, String> feedbackMap;

    // Default Constructor
    public PoseFeedback() {
        feedbackMap = new HashMap<>();
        initializeFeedback();
    }

    /**
     * Helper method to initialize feedback
     */
    private void initializeFeedback() {
        feedbackMap.put("excellent", "You can move on to the next move!");
        feedbackMap.put("good", "Great Job! Keep up the good work!");
        feedbackMap.put("average", "You're doing well, but there are few improvements needed!");
        feedbackMap.put("poor", "Keep practicing, try to focus on key movements for better alignment!");
    }

    /**
     * Method to print feedback
     * 
     * @param score User score
     */
    public String provideFeedback(int score) {
        // Provide feedback based on score range
        // Case 1: Score >= 90
        if (score >= 90) {
            return feedbackMap.get("excellent");
        }
        // Case 2: 80 <= Score < 90
        else if (score >= 80) {
            return feedbackMap.get("good");
        }
        // Case 3: 70 <= Score < 80
        else if (score >= 70) {
            return feedbackMap.get("average");
        }
        // Case 4: Score < 70
        else {
            return feedbackMap.get("poor");
        }
    }

    /**
     * Method to get feedback for body part
     * 
     * @param score    User score
     * @param bodyPart Body part working on
     */
    public String provideSpecificFeedback(int score, String bodyPart) {
        String baseFeedBack = provideFeedback(score);

        if (score < 90) {
            switch (bodyPart) {
                case "nose":
                    return baseFeedBack + " Focus on your head placement for improvement.";
                default:
                    return baseFeedBack + " Focus on your " + bodyPart + " for improvement.";
            }
        }

        // User ready to move on to next move, score >= 90
        return baseFeedBack;
    }
}

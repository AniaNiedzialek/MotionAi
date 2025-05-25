package com.instructor.main;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Scanner;
import java.util.Set;

import com.instructor.algorithms.DynamicTimeWarping;
import com.instructor.controller.ApplicationHandler;
import com.instructor.controller.FileCleanup;
import com.instructor.data.PoseDataProcessing;
import com.instructor.data.PoseDataReader;
import com.instructor.evaluation.PoseFeedback;
import com.instructor.evaluation.PoseScoring;

public class Main {
    public static void main(String[] args) {
        // Initialize FileCleanup to clean up saved filenames
        FileCleanup fileCleanup = new FileCleanup();
        Set<String> userHistory = new HashSet<>(); // Initialize Set to store user history
        userHistory = fileCleanup.getExistingFilenames(); // Store user performance history

        // Instantiate PoseDataReader and PoseDataProcessing and Pose Scoring and Pose
        // Feedback
        PoseDataReader poseDataReader = new PoseDataReader();
        PoseDataProcessing poseDataProcessing = new PoseDataProcessing();
        PoseScoring poseScoring = new PoseScoring();
        PoseFeedback poseFeedback = new PoseFeedback();

        // Map <Keypoints (ex: left_leg), Map<Frame (ex: 1), coordinates (x,y,z)>>
        // Instantiate Hashmap to store user key points
        Map<String, Map<Integer, float[]>> userKeypointsMap = new HashMap<>();
        Map<String, Map<Integer, float[]>> proKeypointsMap = new HashMap<>();

        // Create the entry point for communication
        ApplicationHandler handler = new ApplicationHandler();

        // Create a Scanner object for user input
        Scanner scanner = new Scanner(System.in);
        boolean running = true;

        while (running) { // Main loop for user interaction
            // User input options
            System.out.println();
            System.out.println("Please select options below:");
            System.out.println("1: Record video.");
            System.out.println("2: Upload video.");
            System.out.println("3: User history.");
            System.out.println("0: Test.");
            System.out.println("4: Exit."); // Added exit option

            int option = scanner.nextInt();
            scanner.nextLine(); // Skip

            switch (option) {
                case 1: // Capture user video
                    System.out.println("Starting video capture from Python...");
                    if (handler.runCapturePoseEstimation("beginner")) {
                        // Update user history
                        fileCleanup.updateSavedFilenamesFile();

                        // Process user video to get data
                        userKeypointsMap = poseDataReader.readUserFile();

                        // Process user data
                        userKeypointsMap = poseDataProcessing.processPoseData(userKeypointsMap);
                    } else {
                        System.out.println("Video capture failed. Please try again.");
                    }
                    break;

                case 2: // Get user uploaded video
                    System.out.println("Enter the path for the user keypoints file: ");
                    String userFile = scanner.nextLine(); // Assign value to userFile

                    // Ensure a valid .mp4 file path is provided
                    while (userFile == null || userFile.isEmpty() || !userFile.endsWith(".mp4")) {
                        System.out.println("No valid user file path provided");
                        System.out.println("Enter the path for the user keypoints file: ");
                        userFile = scanner.nextLine(); // Assign value to userFile
                    }

                    // Allow user to upload video to be compared
                    handler.runUploadPoseEstimation(userFile, "Beginner");

                    // Update user history
                    fileCleanup.updateSavedFilenamesFile();

                    // Process user video to get data
                    userKeypointsMap = poseDataReader.readUserFile();

                    // Process user data
                    userKeypointsMap = poseDataProcessing.processPoseData(userKeypointsMap);
                    break;

                case 3: // Get user history performance
                    System.out.println("User history: ");
                    // Refresh user history to get the latest data from the file
                    userHistory = fileCleanup.getExistingFilenames();

                    if (userHistory.isEmpty()) {
                        System.out.println("No saved files found in history");
                    } else {
                        for (String filename : userHistory) {
                            System.out.println("- " + filename);
                        }
                    }
                    break;

                case 0: // Test
                    // Load keypoints from files
                    userKeypointsMap = poseDataReader
                            .readKeypointsFromFile("./motion_database/ballet_spin/beginner.txt");
                    proKeypointsMap = poseDataReader
                            .readKeypointsFromFile("./motion_database/ballet_spin/pro.txt");

                    userKeypointsMap = poseDataProcessing.processPoseData(userKeypointsMap);
                    proKeypointsMap = poseDataProcessing.processPoseData(proKeypointsMap);

                    // Calculate similarity score between user and pro based on total distance
                    // difference
                    float similarityScore = DynamicTimeWarping.totalDtw(userKeypointsMap, proKeypointsMap);

                    // Assume max similarity and calculate total score
                    float maxSimilarity = 4.0f; // Replace with actual value

                    // DTW Score
                    int finalScore = poseScoring.calculateScore(similarityScore, maxSimilarity);

                    // Output similarity score and final score overall
                    System.out.println();

                    System.out.println("Final Score (out of 100): " + finalScore);
                    System.out.println();

                    System.out.println(poseFeedback.provideFeedback(finalScore)); // Display feedback based on score
                    System.out.println();

                    System.out.println("Shoulder Left: ");
                    String prompt1 = poseScoring.generateComparisonPrompt(userKeypointsMap, proKeypointsMap,
                            "shoulder_left");
                    System.out.println(handler.generateFeedbackAPI(prompt1)); // Test API call

                    System.out.println();

                    break;

                case 4: // Exit
                    running = false; // Exit the loop
                    System.out.println("Exiting the application.");
                    break;

                default:
                    System.out.println("Invalid option, please try again.");
                    break;
            }
        }

        scanner.close();
    }
}

package com.instructor.data;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

public class PoseDataReader {

    /**
     * Method to read keypoints data from a text file, takes a file path as an
     * argument
     * Stores frame numbers and their corresponding x,y,z coordinates
     * 
     * @param filePath Text file that contains user keypoints data
     * @return Map where the key is the keypoint name, and the value is another Map
     *         of frame value and coordinates
     */
    public Map<String, Map<Integer, float[]>> readKeypointsFromFile(String filePath) {
        // The outer Map holds keypoint names as keys and a Map of frame data as values
        Map<String, Map<Integer, float[]>> keypointsMap = new HashMap<>();

        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
            String line;
            String currentKeypoint = null; // Track current keypoint being processed

            // Read each line from the file
            while ((line = reader.readLine()) != null) {
                // Trim whitespace from the line
                line = line.trim();

                // If the line ends with a colon, it indicates a new keypoint
                if (line.endsWith(":")) {
                    // Extract keypoint name (removing colon at the end)
                    currentKeypoint = line.substring(0, line.length() - 1).trim();

                    // Initialize a new Map to store frame data for the keypoint
                    keypointsMap.put(currentKeypoint, new HashMap<>());

                } else if (currentKeypoint != null) {
                    // Line should be in the format: Frame x: x=val, y=val, z=val
                    String[] frameParts = line.split(":");

                    if (frameParts.length > 1) {
                        // Extract the frame number from the line (Frame 1)
                        String frameInfo = frameParts[0].trim();
                        int frameNumber = Integer.parseInt(frameInfo.split(" ")[1]);

                        // Extract x, y, z coordinates
                        String[] coordinates = frameParts[1].trim().split(",");
                        float[] values = new float[3]; // Hold x, y, z values

                        // Parse the x, y, z values and store them in the values array
                        for (int i = 0; i < coordinates.length; i++) {
                            String[] coord = coordinates[i].trim().split("=");
                            values[i] = Float.parseFloat(coord[1].trim());
                        }
                        // Add the parsed frame data to the current keypoints' Map
                        keypointsMap.get(currentKeypoint).put(frameNumber, values);
                    }
                }
            }
        } catch (Exception e) {
            // Print stack trace if error occurs
            e.printStackTrace();
        }
        // Return fully populated Map of keypoints and frame data
        return keypointsMap;
    }

    /**
     * Method to display pose keypoints data by reading from a file and display all
     * value
     * 
     * @param userKeypointsMap Map contain all information about user keypoints,
     *                         frame, coordinates
     */
    public void displayPoseData(Map<String, Map<Integer, float[]>> userKeypointsMap) {
        // Read the keypoints data from the file
        Map<String, Map<Integer, float[]>> keypointsData = userKeypointsMap;
        System.out.println("Received Pose Data:");

        // Iterate through the keypoints and display their frame data
        for (String keypoint : keypointsData.keySet()) {
            System.out.println(keypoint + ":");
            Map<Integer, float[]> frames = keypointsData.get(keypoint);

            // For each keypoint, retrieve and print the frame number and coordinates
            for (Integer frame : frames.keySet()) {
                float[] coordinates = frames.get(frame);
                System.out.printf("  Frame %d: x=%.4f, y=%.4f, z=%.4f%n", frame, coordinates[0], coordinates[1],
                        coordinates[2]);
            }
        }
    }

    /**
     * Method to get the most recent file created by user from file name list
     * 
     * @param filePath Location of txt file containing user generated file
     * @return Most recent file name
     */
    public String readLastSavedFileName(String filePath) {
        String lastLine = null;

        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
            String currentLine;

            while ((currentLine = reader.readLine()) != null) {
                lastLine = currentLine; // Keep updating lastLine until end of file
            }
        } catch (IOException e) {
            System.err.println("Error reading the last saved file name: " + e.getMessage());
        }
        return lastLine;
    }

    /**
     * Method to process the user file for pose estimation
     * 
     * @return Updated map of user keypoints
     */
    public Map<String, Map<Integer, float[]>> readUserFile() {
        Map<String, Map<Integer, float[]>> userKeypointsMap = new HashMap<>(); // Initialize map to store user
                                                                               // data

        // Read the last saved filename from last_saved_filename.txt
        String keypointsFileName = readLastSavedFileName("last_saved_filename.txt");

        if (keypointsFileName != null) {
            // Use the file name to read keypoints from the newly created file
            userKeypointsMap = readKeypointsFromFile(keypointsFileName);

            // Process the keypoints map as needed
            System.out.println("Successfully read keypoints from: " + keypointsFileName);
        } else {
            System.out.println("Failed to read the keypoints file name.");
        }

        return userKeypointsMap; // Return the populated map
    }
}

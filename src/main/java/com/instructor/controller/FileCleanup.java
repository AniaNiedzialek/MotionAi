package com.instructor.controller;

import java.io.*;
import java.nio.file.*;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;

public class FileCleanup {
    // A Set to store unique filenames that have been saved
    private Set<String> existingFilenames;

    // Path to the file where the last saved filenames are stored
    private final String savedFilenamesFilePath = "last_saved_filename.txt";

    // Constructor to initialize the filenames and perform cleanup
    public FileCleanup() {
        this.existingFilenames = loadSavedFilenames();
        cleanupExistingFilenames();
    }

    /**
     * Reads saved filenames form "last_saved_filename.txt" and loads them into a
     * Set.
     * Helps avoid duplicate entries and allows quick lookup.
     * 
     * @return Set of filenames that were saved previously.
     */
    public Set<String> loadSavedFilenames() {
        Set<String> filenames = new HashSet<>();

        try (BufferedReader reader = new BufferedReader(new FileReader(savedFilenamesFilePath))) {
            String line;

            while ((line = reader.readLine()) != null) {
                filenames.add(line);
            }
        } catch (IOException e) {
            System.out.println("Error reading saved filenames file: " + e.getMessage());
        }
        return filenames;
    }

    /**
     * Iterates through the Set of existing filenames, removing any that no longer
     * exists on the file system. This keep the list of filenames accurate and
     * up-to-date.
     */
    public void cleanupExistingFilenames() {
        Iterator<String> iterator = existingFilenames.iterator();

        while (iterator.hasNext()) {
            String filename = iterator.next();

            if (!Files.exists(Paths.get(filename))) {
                iterator.remove(); // Remove non-existing file from the Set
            }
        }
        updateSavedFilenamesFile();
    }

    /**
     * Writes the current list of valid filenames back to "last_saved_filename.txt".
     * This ensures that the shared file accurately reflects only existing files.
     */
    public void updateSavedFilenamesFile() {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(savedFilenamesFilePath))) {
            for (String filename : existingFilenames) {
                writer.write(filename);
                writer.newLine();
            }
        } catch (IOException e) {
            System.out.println("Error updating saved filenames file: " + e.getMessage());
        }
    }

    public Set<String> getExistingFilenames() {
        return this.existingFilenames;
    }
}

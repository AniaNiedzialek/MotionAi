package com.instructor.algorithms;

import java.util.List;

public class InsertionSort {
    /**
     * Sorts a portion of a list using the insertion sort algorithm. The sorting
     * occurs in-place between the indices specified by `left` and `right`.
     *
     * @param list      The list to be sorted.
     * @param left      The starting index of the sublist to be sorted.
     * @param right     The ending index of the sublist to be sorted.
     * @param ascending True if the list should be sorted in ascending order,
     *                  false for descending order.
     * @param <T>       The type of elements in the list, which must be comparable.
     */
    public static <T extends Comparable<T>> void insertionSort(List<T> list, int left, int right, boolean ascending) {
        // Start at the second element (index 1)
        for (int i = left + 1; i <= right; i++) {
            T key = list.get(i); // Element to be inserted
            int j = i - 1; // Index of the previous element

            // Find the correct position to insert the element
            while (j >= left && ((ascending && list.get(j).compareTo(key) > 0)
                    || (!ascending && list.get(j).compareTo(key) < 0))) {
                list.set(j + 1, list.get(j)); // Shift elements to the right
                j--; // Move to the left
            }

            list.set(j + 1, key); // Insert the element
        }
    }
}

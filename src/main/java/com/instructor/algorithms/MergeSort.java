package com.instructor.algorithms;

import java.util.List;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.RecursiveAction;

public class MergeSort {
    private static final ForkJoinPool pool = ForkJoinPool.commonPool(); // Global thread pool
    private static final int THRESHOLD = 20; // Threshold for insertion sort

    /**
     * Sorts a list of integers in ascending order using the merge sort algorithm.
     * This method serves as an entry point that initializes the recursive sorting
     * process.
     *
     * @param list The list of integers to be sorted. The list is sorted in-place.
     */
    public static <T extends Comparable<T>> void mergeSort(List<T> list, boolean ascending) {
        if (list.size() <= 1) {
            return; // Base case: a list of size 0 or 1 is already sorted
        }

        pool.invoke(new MergeSortTask<>(list, 0, list.size() - 1, ascending));
    }

    private static class MergeSortTask<T extends Comparable<T>> extends RecursiveAction {
        private final List<T> list;
        private final int left;
        private final int right;
        private final boolean ascending;

        public MergeSortTask(List<T> list, int left, int right, boolean ascending) {
            this.list = list;
            this.left = left;
            this.right = right;
            this.ascending = ascending;
        }

        @Override
        protected void compute() {
            if (right - left + 1 <= THRESHOLD) { // If sublist size <= threshold, use insertion sort
                InsertionSort.insertionSort(list, left, right, ascending);
                return;
            }

            int mid = (left + right) / 2;

            // Create subtasks for left and right sublists
            MergeSortTask<T> leftTask = new MergeSortTask<>(list, left, mid, ascending);
            MergeSortTask<T> rightTask = new MergeSortTask<>(list, mid + 1, right, ascending);

            // Invoke subtasks in parallel
            invokeAll(leftTask, rightTask);

            // Merge sorted sublists
            merge(list, left, mid, right, ascending);

        }
    }

    /**
     * Merges two contiguous sublists within the given list in place. The sublists
     * are defined by the indices [left, mid] and [mid+1, right]. This method
     * assumes that both sublists are already sorted and merges them into a single
     * sorted sublist.
     *
     * @param list      The list containing the sublists to be merged.
     * @param left      The starting index of the first sublist.
     * @param mid       The ending index of the first sublist, which is also one
     *                  less
     *                  than the starting index of the second sublist.
     * @param right     The ending index of the second sublist.
     * @param ascending True if ascending, false if descending
     */
    private static <T extends Comparable<T>> void merge(List<T> list, int left, int mid, int right, boolean ascending) {
        int i = left; // Left sublist pointer
        int j = mid + 1; // Right sublist pointer

        // Iterate over the left and right sublists to merge
        while (i <= mid && j <= right) {
            // Determine if ascending or descending
            if ((ascending && list.get(i).compareTo(list.get(j)) <= 0)
                    || (!ascending && list.get(i).compareTo(list.get(j)) >= 0)) {
                i++; // Already sorted
            } else {
                // Left > Right Ascending, Right > Left Descending
                T temp = list.get(j); // Store element
                list.remove(j); // Remove element
                list.add(i, temp); // Add right element to the left sublist

                i++;
                mid++;
                j++;
            }
        }
    }
}

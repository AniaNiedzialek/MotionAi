package com.instructor.main;

import javafx.application.Application;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;
import javafx.scene.text.Font;
import javafx.stage.Stage;

public class DanceInstructorUI extends Application {

    private Scene mainScene;
    private Button startButton;
    private Button inputFileButton;
    private Button doneButton;
    private Button userButton;
    private Button profButton;
    private Button backButton;

    @Override
    public void start(Stage primaryStage) {

        // Main Screen
        BorderPane mainLayout = new BorderPane();
        mainLayout.setPadding(new Insets(20));
        mainLayout.setStyle("-fx-background-color: #2B2B2B;");

        Label title = new Label("Motion AI");
        title.setFont(new Font("Georgia", 30));
        title.setTextFill(Color.WHITE);

        Label description = new Label("Compare your moves to the pros and get detailed feedback.");
        description.setFont(new Font("Georgia", 20));
        description.setTextFill(Color.LIGHTGRAY);

        // Button Controls
        startButton = new Button("Start Recording");
        startButton.setPrefWidth(180);
        startButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia';-fx-font-size: 20px;");
        startButton.setOnMouseEntered(e -> startButton.setStyle(
                "-fx-background-color: #5A5A5A; -fx-text-fill: lightgray; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));
        startButton.setOnMouseExited(e -> startButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));

        inputFileButton = new Button("Input File");
        inputFileButton.setPrefWidth(180);
        inputFileButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia';-fx-font-size: 20px;");
        inputFileButton.setOnMouseEntered(e -> inputFileButton.setStyle(
                "-fx-background-color: #5A5A5A; -fx-text-fill: lightgray; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));
        inputFileButton.setOnMouseExited(e -> inputFileButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));

        doneButton = new Button("Start Analysis");
        doneButton.setPrefWidth(180);
        doneButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia';-fx-font-size: 20px;");
        doneButton.setOnMouseEntered(e -> doneButton.setStyle(
                "-fx-background-color: #5A5A5A; -fx-text-fill: lightgray; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));
        doneButton.setOnMouseExited(e -> doneButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));

        userButton = new Button("User");
        userButton.setPrefWidth(180);
        userButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia';-fx-font-size: 20px;");
        userButton.setOnMouseEntered(e -> userButton.setStyle(
                "-fx-background-color: #5A5A5A; -fx-text-fill: lightgray; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));
        userButton.setOnMouseExited(e -> userButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));

        profButton = new Button("Pro");
        profButton.setPrefWidth(180);
        profButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia';-fx-font-size: 20px;");
        profButton.setOnMouseEntered(e -> profButton.setStyle(
                "-fx-background-color: #5A5A5A; -fx-text-fill: lightgray; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));
        profButton.setOnMouseExited(e -> profButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));

        backButton = new Button("Back");
        backButton.setPrefWidth(180);
        backButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia';-fx-font-size: 20px;");
        backButton.setOnMouseEntered(e -> backButton.setStyle(
                "-fx-background-color: #5A5A5A; -fx-text-fill: lightgray; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));
        backButton.setOnMouseExited(e -> backButton.setStyle(
                "-fx-background-color: #3E3E3E; -fx-text-fill: white; -fx-font-family: 'Georgia'; -fx-font-size: 20px;"));

        // Event Handlers
        DanceInstructorUIController controller = new DanceInstructorUIController(primaryStage, startButton,
                inputFileButton, doneButton, userButton, profButton, backButton);

        // VBox for instructions
        VBox instructionsVbox = new VBox(20);
        instructionsVbox.setPadding(new Insets(15));
        instructionsVbox.setAlignment(Pos.CENTER);

        HBox buttonBox = new HBox(10, userButton, profButton);
        buttonBox.setAlignment(Pos.CENTER);

        instructionsVbox.getChildren().addAll(title, description, buttonBox, doneButton);

        // Add elements to main layout
        mainLayout.setCenter(instructionsVbox);

        mainScene = new Scene(mainLayout, 600, 400);

        controller.setMainScene(mainScene);

        // Set up the stage
        primaryStage.setTitle("Camera Input App");
        primaryStage.setScene(mainScene);
        primaryStage.show();
    }

    public static void main(String[] args) {
        launch(args);

    }
}
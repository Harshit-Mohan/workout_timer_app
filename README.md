# Shared Workout Timer

A real-time, synchronized workout timer built with Python (Flask + Socket.IO). Designed for partners to workout together remotely, keeping the timer, exercises, and audio cues perfectly in sync across multiple devices.

## Features

*   **Real-Time Synchronization:** Timer state is shared instantly. If one person pauses, it pauses for everyone.
*   **Text-to-Speech (TTS):** Announces the current exercise and what's coming up next during rest periods.
*   **Audio Cues:** Beeps for start, rest, and countdowns (3-2-1).
*   **Custom Routine Editor:** Create and modify workouts directly from the browser.
*   **Mobile Friendly:** Responsive UI with large buttons and high contrast for visibility during workouts.
*   **Keyboard Shortcuts:** Control the timer without touching the screen.
*   **Persistence:** Custom routines are saved to your browser and synced to the server automatically.

## Installation & Local Usage

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application:**
    ```bash
    python main.py
    ```

3.  **Access:**
    Open your browser to `http://localhost:5000`.

## Deployment

### Google Cloud Run (Recommended)
This allows you to have a permanent public URL to share.

1.  Install the Google Cloud CLI.
2.  Run the deploy command:
    ```bash
    gcloud run deploy workout-timer --source . --max-instances=1 --allow-unauthenticated --region us-central1
    ```
    *Note: `--max-instances=1` is crucial to ensure all users connect to the same timer instance.*

### ngrok (Temporary / No Cloud Account)
If you just want to share it quickly from your laptop:

1.  Start the app locally (`python main.py`).
2.  Run ngrok:
    ```bash
    ngrok http 5000
    ```
3.  Share the generated `https://...ngrok-free.app` link.

## User Guide

### Workout Controls
Once a workout is started, the following controls are available:

| Button | Keyboard Key | Description |
| :--- | :--- | :--- |
| **⏮ PREV** | `Left Arrow` | Go back to the previous exercise. |
| **⏯ PAUSE** | `Spacebar` | Pause or Resume the timer for everyone. |
| **NEXT ⏭** | `Right Arrow` | Skip the current exercise or rest period. |
| **✕ QUIT** | `Esc` | Exit the workout and return to the main menu. |

### The Display
*   **Green Background:** Active work period.
*   **Blue Background:** Rest period.
*   **Yellow Background:** Preparation period (Get Ready).
*   **Next Exercise:** During rest, the name of the upcoming exercise is displayed below the timer.

## How to Use the Editor

Click the **"🛠 MODIFY / ADD ROUTINES"** button on the main menu to open the editor. The editor is split into two parts:

### 1. Edit Exercises (Base Routines)
This is where you define the actual list of exercises (e.g., "Leg Day", "Abs", "Warmup").

1.  **Select Routine:** Choose an existing routine to edit, or leave it as `-- New Routine --` to create one.
2.  **Routine Name:** Give it a unique ID (e.g., `chest_day`).
3.  **Add Exercise Step:** Click to add a new row.
    *   **Name:** The text displayed (e.g., "Pushups").
    *   **Secs:** Duration in seconds. Leave empty for "Manual" mode (waits for you to press Next).
    *   **Type:**
        *   `Work`: Green background, start beep.
        *   `Rest`: Blue background, rest beep.
        *   `Prep`: Yellow background, used for "Get Ready".
        *   `Manual`: Green background, no timer (reps based).
4.  **Save:** Click "SAVE EXERCISES".

### 2. Create Workout Menu Item
This is where you create the buttons that appear on the main menu. A "Workout" is a combination of one or more "Base Routines".

*Example: A "Full Body" workout might consist of [Warmup] + [Main Routine] + [Abs].*

1.  **Select Workout:** Choose an existing menu item or create a new one.
2.  **ID:** A unique internal name (e.g., `full_body`).
3.  **Display Label:** The text shown on the big button (e.g., "FULL BODY BLAST").
4.  **Include Routines:** Check the boxes for the Base Routines you want to include in this workout. The order matters!
5.  **Save:** Click "SAVE WORKOUT MENU".

### Data Persistence
*   **Locally:** Changes are saved to `workout_data.json`.
*   **On Cloud:** Changes are saved to your browser's Local Storage. When you reload the app or the server restarts, your browser automatically sends your custom routines back to the server to restore them.

## Project Structure

*   `main.py`: The Flask backend server. Handles the timer logic, socket events, and state management.
*   `templates/index.html`: The frontend UI. Handles display, audio generation, and user input.
*   `Dockerfile`: Configuration for deploying to Google Cloud Run.
*   `requirements.txt`: Python dependencies.

## License

This project is open source. Feel free to modify and distribute.
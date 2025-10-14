import json
import os

#HISTORY_FILE = "history.json"
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")

def save_history_to_json(timestamp, frequency, stroke):
    """Saves history to a JSON file."""
    history_data = []

    # Check if file exists
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history_data = json.load(file)  # Load existing history
            except json.JSONDecodeError:
                history_data = []  # Reset if there's an issue

    # Append new entry
    history_data.append({
        "timestamp": timestamp,
        "frequency": frequency,
        "stroke": stroke
    })

    # Debugging: Print the JSON path
    print(f"Saving to: {os.path.abspath(HISTORY_FILE)}")

    # Write updated history to file
    with open(HISTORY_FILE, "w") as file:
        json.dump(history_data, file, indent=4)


def load_history_from_json():
    """Loads history from the JSON file and returns it as a list."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                return json.load(file)  # Return loaded history
            except json.JSONDecodeError:
                return []
    return []

def delete_history_entry(timestamp):
    """Deletes an entry from the JSON file based on the timestamp."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            try:
                history_data = json.load(file)
            except json.JSONDecodeError:
                history_data = []

        # Remove the entry that matches the timestamp
        updated_history = [entry for entry in history_data if entry["timestamp"] != timestamp]

        # Save updated history back to file
        with open(HISTORY_FILE, "w") as file:
            json.dump(updated_history, file, indent=4)

        return True  # Entry successfully deleted
    return False  # File not found or no entry deleted

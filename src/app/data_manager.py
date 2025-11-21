import json
import os
from datetime import datetime

LOG_FILE = 'data/logs/usage_logs.json'
NOTES_FILE = 'data/notes.json'

def log_interaction(username, sentence, processed_sentence):
    """Logs the user's sentence and the processed pictograms to a JSON file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'username': username,
        'sentence': sentence,
        'processed_sentence': processed_sentence
    }
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except IOError as e:
        print(f"Error writing to log file: {e}")

def get_notes():
    """Retrieves all notes from the notes file."""
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_note(author, text):
    """Saves a new note to the notes file."""
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    notes = get_notes()
    new_note = {
        'timestamp': datetime.now().isoformat(),
        'author': author,
        'text': text
    }
    notes.append(new_note)
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    # Example usage
    log_interaction("Hola", [{'word': 'Hola', 'pictogram': 'path/to/hola.png'}])
    save_note("test_user", "This is a test note.")
    print(f"Check the log file at: {LOG_FILE}")
    print(f"Check the notes file at: {NOTES_FILE}")
    print(get_notes())


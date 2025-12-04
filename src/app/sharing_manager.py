import json
import os
import uuid
from datetime import datetime
from typing import Dict, List

SHARED_NOTES_FILE = os.path.join('data', 'shared_notes.json')


def _load() -> List[Dict]:
    if not os.path.exists(SHARED_NOTES_FILE):
        return []
    with open(SHARED_NOTES_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save(data: List[Dict]):
    os.makedirs(os.path.dirname(SHARED_NOTES_FILE), exist_ok=True)
    with open(SHARED_NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_shared_note(author: str, student: str, content: str, shared_with: List[str]) -> Dict:
    note = {
        'id': str(uuid.uuid4()),
        'author': author,
        'student': student,
        'content': content,
        'shared_with': shared_with,
        'created_at': datetime.utcnow().isoformat(),
        'read_by': []
    }
    notes = _load()
    notes.append(note)
    _save(notes)
    return note


def list_shared_notes(username: str) -> List[Dict]:
    notes = _load()
    accessible = []
    for note in notes:
        if note['author'] == username or username in note['shared_with'] or note['student'] == username:
            accessible.append(note)
    return accessible


def acknowledge_note(note_id: str, username: str):
    notes = _load()
    for note in notes:
        if note['id'] == note_id:
            readers = set(note.get('read_by', []))
            readers.add(username)
            note['read_by'] = list(readers)
            break
    _save(notes)


def delete_shared_note(note_id: str, username: str):
    notes = _load()
    notes = [note for note in notes if not (note['id'] == note_id and note['author'] == username)]
    _save(notes)

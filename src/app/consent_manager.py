import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import HTTPException

CONSENT_FILE = os.path.join('data', 'consents.json')
DATA_EXPORT_DIR = os.path.join('data', 'exports')
AUDIT_LOG = os.path.join('data', 'logs', 'audit_logs.json')


def _load_consents() -> List[Dict]:
    if not os.path.exists(CONSENT_FILE):
        return []
    with open(CONSENT_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_consents(data: List[Dict]):
    os.makedirs(os.path.dirname(CONSENT_FILE), exist_ok=True)
    with open(CONSENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_consent(username: str, guardian: str, scope: List[str]) -> Dict:
    consents = [c for c in _load_consents() if c['username'] != username]
    consent = {
        'id': str(uuid.uuid4()),
        'username': username,
        'guardian': guardian,
        'scope': scope,
        'timestamp': datetime.utcnow().isoformat()
    }
    consents.append(consent)
    _save_consents(consents)
    return consent


def get_consent(username: str) -> Optional[Dict]:
    return next((c for c in _load_consents() if c['username'] == username), None)


def log_audit(action: str, actor: str, target: Optional[str] = None, metadata: Optional[Dict] = None):
    entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'actor': actor,
        'target': target,
        'metadata': metadata or {}
    }
    os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
    with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def export_user_data(username: str) -> str:
    from src.app import data_manager

    os.makedirs(DATA_EXPORT_DIR, exist_ok=True)
    export_path = os.path.join(DATA_EXPORT_DIR, f"export_{username}_{datetime.utcnow().timestamp():.0f}.json")

    logs = []
    if os.path.exists(data_manager.LOG_FILE):
        with open(data_manager.LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get('username') == username:
                    logs.append(entry)

    notes = [note for note in data_manager.get_notes() if note.get('author') == username]
    assignments = [assignment for assignment in data_manager.get_assignments() if assignment.get('author') == username]

    payload = {
        'username': username,
        'logs': logs,
        'notes': notes,
        'assignments': assignments,
        'exported_at': datetime.utcnow().isoformat()
    }
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return export_path


def delete_user_data(username: str):
    from src.app import data_manager

    if os.path.exists(data_manager.LOG_FILE):
        with open(data_manager.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(data_manager.LOG_FILE, 'w', encoding='utf-8') as f:
            for line in lines:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get('username') != username:
                    f.write(json.dumps(obj, ensure_ascii=False) + '\n')

    remaining_notes = [note for note in data_manager.get_notes() if note.get('author') != username]
    with open(data_manager.NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(remaining_notes, f, ensure_ascii=False, indent=2)

    remaining_assignments = [assignment for assignment in data_manager.get_assignments() if assignment.get('author') != username]
    with open(data_manager.ASSIGNMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(remaining_assignments, f, ensure_ascii=False, indent=2)

    log_audit('delete_user_data', username)


def ensure_consent(username: str):
    consent = get_consent(username)
    if not consent:
        raise HTTPException(status_code=403, detail="Consentimiento faltante para este usuario")

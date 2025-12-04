import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any

from fastapi import UploadFile

try:
    from faster_whisper import WhisperModel  # type: ignore
except ImportError:  # pragma: no cover
    WhisperModel = None  # type: ignore

AUDIO_DIR = os.path.join('data', 'audio')
AUDIO_META_FILE = os.path.join('data', 'audio_logs.json')
AUDIO_CUES_DIR = os.path.join('data', 'audio_cues')
AUDIO_CUES_META = os.path.join('data', 'audio_cues.json')

MODEL_SIZE = os.environ.get('STT_MODEL_SIZE', 'base')
_model: Any = None

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def _load_meta(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _save_meta(file_path: str, data: List[Dict]):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _get_model() -> Any:
    global _model
    if WhisperModel is None:
        return None
    if _model is None:
        _model = WhisperModel(MODEL_SIZE, device=os.environ.get('STT_DEVICE', 'cpu'))
    return _model

def save_uploaded_audio(username: str, file: UploadFile, label: Optional[str] = None) -> Dict:
    _ensure_dir(AUDIO_DIR)
    suffix = os.path.splitext(file.filename or '')[1] or '.wav'
    audio_id = str(uuid.uuid4())
    file_path = os.path.join(AUDIO_DIR, f"{audio_id}{suffix}")
    file.file.seek(0)
    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    metadata = _load_meta(AUDIO_META_FILE)
    entry = {
        'id': audio_id,
        'username': username,
        'label': label,
        'filename': os.path.basename(file_path),
        'stored_path': file_path,
        'uploaded_at': datetime.utcnow().isoformat()
    }
    metadata.append(entry)
    _save_meta(AUDIO_META_FILE, metadata)
    return entry

def transcribe_audio(file_path: str, language: str = 'es') -> Dict:
    model = _get_model()
    if model is None:  # pragma: no cover
        return {
            'text': '',
            'language': language,
            'warnings': ['transcription_model_missing']
        }
    segments, _ = model.transcribe(file_path, language=language, beam_size=5)
    transcript = ''.join(segment.text for segment in segments).strip()
    return {
        'text': transcript,
        'language': language,
        'warnings': []
    }

def list_audio_uploads() -> List[Dict]:
    return _load_meta(AUDIO_META_FILE)

def register_audio_cue(title: str, tags: List[str], author: str, file: UploadFile, description: Optional[str] = None) -> Dict:
    _ensure_dir(AUDIO_CUES_DIR)
    suffix = os.path.splitext(file.filename or '')[1] or '.mp3'
    cue_id = str(uuid.uuid4())
    file_path = os.path.join(AUDIO_CUES_DIR, f"{cue_id}{suffix}")
    file.file.seek(0)
    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    metadata = _load_meta(AUDIO_CUES_META)
    entry = {
        'id': cue_id,
        'title': title,
        'description': description,
        'tags': tags,
        'author': author,
        'filename': os.path.basename(file_path),
        'stored_path': file_path,
        'created_at': datetime.utcnow().isoformat()
    }
    metadata.append(entry)
    _save_meta(AUDIO_CUES_META, metadata)
    return entry

def list_audio_cues() -> List[Dict]:
    return _load_meta(AUDIO_CUES_META)

def get_audio_cue(cue_id: str) -> Optional[Dict]:
    return next((cue for cue in list_audio_cues() if cue['id'] == cue_id), None)

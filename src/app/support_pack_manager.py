import json
import os
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Optional

DEFAULT_PACKS_DIR = os.path.join('data', 'support_packs')
ACTIVE_PACK_FILE = os.path.join('data', 'active_support_pack.json')
PACK_INDEX_FILE = os.path.join(DEFAULT_PACKS_DIR, 'index.json')


def _ensure_dir():
    os.makedirs(DEFAULT_PACKS_DIR, exist_ok=True)


def _load_index() -> List[Dict]:
    if not os.path.exists(PACK_INDEX_FILE):
        return []
    with open(PACK_INDEX_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_index(packs: List[Dict]):
    _ensure_dir()
    with open(PACK_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(packs, f, ensure_ascii=False, indent=2)


def list_packs() -> List[Dict]:
    return _load_index()


def get_pack(pack_id: str) -> Optional[Dict]:
    return next((pack for pack in list_packs() if pack['id'] == pack_id), None)


def save_pack(author: str, payload: Dict, pack_id: Optional[str] = None) -> Dict:
    _ensure_dir()
    packs = _load_index()
    if pack_id:
        pack = get_pack(pack_id)
        if not pack:
            raise ValueError('Pack not found')
    else:
        pack_id = str(uuid.uuid4())
        pack = None

    pack_file = os.path.join(DEFAULT_PACKS_DIR, f"{pack_id}.json")
    payload_copy = deepcopy(payload)
    with open(pack_file, 'w', encoding='utf-8') as f:
        json.dump(payload_copy, f, ensure_ascii=False, indent=2)

    entry = {
        'id': pack_id,
        'author': author,
        'title': payload.get('title') or payload.get('name') or f"Pack {pack_id[:8]}",
        'created_at': pack['created_at'] if pack else datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'filename': os.path.basename(pack_file)
    }
    packs = [p for p in packs if p['id'] != pack_id]
    packs.append(entry)
    _save_index(packs)
    return entry


def delete_pack(pack_id: str):
    pack = get_pack(pack_id)
    if not pack:
        return
    packs = [p for p in list_packs() if p['id'] != pack_id]
    _save_index(packs)
    pack_file = os.path.join(DEFAULT_PACKS_DIR, pack['filename'])
    if os.path.exists(pack_file):
        os.remove(pack_file)
    active_pack = load_active_pack()
    if active_pack and active_pack.get('id') == pack_id:
        if os.path.exists(ACTIVE_PACK_FILE):
            os.remove(ACTIVE_PACK_FILE)


def activate_pack(pack_id: str):
    pack = get_pack(pack_id)
    if not pack:
        raise ValueError('Pack not found')
    pack_file = os.path.join(DEFAULT_PACKS_DIR, pack['filename'])
    with open(pack_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    payload = {
        'id': pack_id,
        'metadata': pack,
        'content': data,
        'activated_at': datetime.utcnow().isoformat()
    }
    with open(ACTIVE_PACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_active_pack() -> Optional[Dict]:
    if not os.path.exists(ACTIVE_PACK_FILE):
        return None
    with open(ACTIVE_PACK_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def get_active_content() -> Optional[Dict]:
    active = load_active_pack()
    if not active:
        return None
    return active.get('content')

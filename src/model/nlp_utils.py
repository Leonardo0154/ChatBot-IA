import json
import os
from unidecode import unidecode
import spacy
import re
import numpy as np

try:
    from src.model import picto_encoder
except Exception:  # pragma: no cover - optional
    picto_encoder = None

# Basic normalization helpers to compare text and pictogram keywords
def _normalize(text: str):
    return unidecode(text.lower().strip()) if text else ''

nlp = spacy.load("es_core_news_sm")

def _load_pictograms():
    """Loads pictograms from a JSON file and verifies their existence in an image directory."""
    
    # Construct the absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, '../../data/raw/arasaac_pictograms_es.json')
    images_dir = os.path.join(script_dir, '../../data/raw/ARASAAC_ES')

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    loaded_pictograms = []
    for pictogram_data in data:
        for keyword_entry in pictogram_data.get('keywords', []):
            keyword = keyword_entry.get('keyword')
            if keyword:
                # Build the potential image path
                relative_image_path = os.path.join(keyword[0].upper(), f"{keyword}.png")
                image_path = os.path.join(images_dir, relative_image_path)
                if os.path.exists(image_path):
                    pictogram_data['path'] = relative_image_path
                    loaded_pictograms.append(pictogram_data)
                    # Move to the next pictogram once a valid image is found for any of its keywords
                    break
    return loaded_pictograms

pictograms = _load_pictograms()

# Precompute normalized keyword/tag sets for quick similarity lookup
_PIC_INDEX = []
for pic in pictograms:
    keywords = [kw.get('keyword') for kw in pic.get('keywords', []) if kw.get('keyword')]
    tags = pic.get('tags', []) or []
    norm_set = {_normalize(k) for k in keywords + tags if k}
    _PIC_INDEX.append({
        'path': pic.get('path'),
        'keywords': keywords,
        'norm_set': norm_set,
        'data': pic
    })

_DENSE_INDEX = None
_DENSE_EMB = None
if picto_encoder is not None:
    try:
        _DENSE_INDEX, _DENSE_EMB = picto_encoder.build_dense_index(pictograms)
    except Exception:
        _DENSE_INDEX, _DENSE_EMB = None, None

def find_pictogram(word, pictograms_list):
    """Finds a pictogram for the given word."""
    word_lower = word.lower()
    word_unidecode = unidecode(word_lower)
    
    # 1. Exact match
    for pictogram in pictograms_list:
        for keyword_entry in pictogram.get('keywords', []):
            if keyword_entry.get('keyword', '').lower() == word_lower:
                return pictogram

    # 2. Unidecode match
    for pictogram in pictograms_list:
        for keyword_entry in pictogram.get('keywords', []):
            if unidecode(keyword_entry.get('keyword', '').lower()) == word_unidecode:
                return pictogram

    # 3. Lemma match
    doc = nlp(word_lower)
    lemma = doc[0].lemma_
    if lemma != word_lower:
        for pictogram in pictograms_list:
            for keyword_entry in pictogram.get('keywords', []):
                if keyword_entry.get('keyword', '').lower() == lemma:
                    return pictogram

    # 4. Unidecode lemma match
    if lemma != word_lower:
        unidecode_lemma = unidecode(lemma)
        for pictogram in pictograms_list:
            for keyword_entry in pictogram.get('keywords', []):
                if unidecode(keyword_entry.get('keyword', '').lower()) == unidecode_lemma:
                    return pictogram

    return None


def suggest_pictograms(text: str, top_k: int = 5):
    """Return top pictogram suggestions using dense embeddings when available; fallback to keyword overlap."""
    if not text:
        return []

    # Try dense if built
    if _DENSE_INDEX is not None and _DENSE_EMB is not None and _DENSE_EMB.shape[0] > 0:
        try:
            return picto_encoder.top_k(text, _DENSE_INDEX, _DENSE_EMB, k=top_k)
        except Exception:
            pass

    # Fallback: keyword/tag overlap
    tokens = re.findall(r"[\wáéíóúñü]+", text.lower())
    norm_tokens = {_normalize(t) for t in tokens if t}
    if not norm_tokens:
        return []

    scores = []
    for entry in _PIC_INDEX:
        overlap = norm_tokens & entry['norm_set']
        if not overlap:
            continue
        score = len(overlap) / max(len(norm_tokens), 1)
        scores.append({
            'path': entry['path'],
            'keyword': entry['keywords'][0] if entry['keywords'] else None,
            'score': round(score, 3),
            'overlap': sorted(list(overlap))
        })

    scores.sort(key=lambda x: (-x['score'], x.get('keyword') or ''))
    return scores[:top_k]

def find_word_for_pictogram(path, pictograms_list):
    """Finds the word for a given pictogram path."""
    for pictogram in pictograms_list:
        if pictogram.get('path') == path:
            # Return the first keyword
            return pictogram.get('keywords', [{}])[0].get('keyword')
    return None





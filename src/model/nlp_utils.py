import json
import os
from unidecode import unidecode
import spacy

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

def find_word_for_pictogram(path, pictograms_list):
    """Finds the word for a given pictogram path."""
    for pictogram in pictograms_list:
        if pictogram.get('path') == path:
            # Return the first keyword
            return pictogram.get('keywords', [{}])[0].get('keyword')
    return None





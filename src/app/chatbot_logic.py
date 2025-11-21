from src.model import nlp_utils
import spacy
import os
import random
import re

# Load the spaCy model
nlp = spacy.load("es_core_news_sm")

# Simple game state
game_state = {
    "in_progress": False,
    "correct_answer": None,
    "pictogram_path": None,
    "mode": None,  # "game" or "guided_session"
    "guided_session_words": [],
    "guided_session_step": 0
}

def start_game(category=None):
    """Starts a new game by selecting a random pictogram, optionally from a specific category."""
    global game_state
    
    pictogram_pool = nlp_utils.pictograms
    
    if category:
        pictogram_pool = [p for p in pictogram_pool if any(tag['schema_name'] == category for tag in p.get('tags', []))]
    
    if not pictogram_pool:
        return {"text": f"No pictograms found for category '{category}'.", "pictogram": None}

    pictogram = random.choice([p for p in pictogram_pool if p.get('keywords')])
    
    game_state["in_progress"] = True
    game_state["mode"] = "game"
    game_state["correct_answer"] = pictogram['keywords'][0]['keyword']
    game_state["pictogram_path"] = pictogram['path']
    
    return {
        "text": f"¡Adivina la palabra! (Categoría: {category or 'General'})",
        "pictogram": game_state["pictogram_path"]
    }

def start_guided_session(words):
    """Starts a guided session with a list of words."""
    global game_state
    
    game_state["in_progress"] = True
    game_state["mode"] = "guided_session"
    game_state["guided_session_words"] = words
    game_state["guided_session_step"] = 0
    
    # Set up the first word
    first_word = words[0]
    pictogram = nlp_utils.find_pictogram(first_word, nlp_utils.pictograms)
    game_state["correct_answer"] = first_word
    game_state["pictogram_path"] = pictogram['path'] if pictogram else None

def process_sentence(sentence: str):
    """Processes a sentence, handles game logic, and maps words to pictograms."""
    global game_state
    
    sentence_lower = sentence.lower()

    if game_state["in_progress"]:
        if game_state["mode"] == "game":
            if sentence_lower == game_state["correct_answer"].lower():
                response_text = f"¡Correcto! La palabra es {game_state['correct_answer']}."
                game_state["in_progress"] = False
                return [{'word': response_text, 'pictogram': None}]
            else:
                return [{'word': "Inténtalo de nuevo.", 'pictogram': game_state["pictogram_path"]}]
        
        elif game_state["mode"] == "guided_session":
            if sentence_lower == game_state["correct_answer"].lower():
                game_state["guided_session_step"] += 1
                if game_state["guided_session_step"] < len(game_state["guided_session_words"]):
                    next_word = game_state["guided_session_words"][game_state["guided_session_step"]]
                    pictogram = nlp_utils.find_pictogram(next_word, nlp_utils.pictograms)
                    game_state["correct_answer"] = next_word
                    game_state["pictogram_path"] = pictogram['path'] if pictogram else None
                    return [{'word': "¡Muy bien! Siguiente palabra...", 'pictogram': game_state["pictogram_path"]}]
                else:
                    game_state["in_progress"] = False
                    return [{'word': "¡Felicidades! Has completado la sesión.", 'pictogram': None}]
            else:
                return [{'word': "Inténtalo de nuevo.", 'pictogram': game_state["pictogram_path"]}]

    # Check if the user wants to play a game
    game_match = re.match(r"jugar a (.+)", sentence_lower)
    if game_match:
        category = game_match.group(1)
        game_response = start_game(category)
        return [{'word': game_response['text'], 'pictogram': game_response['pictogram']}]
    elif any(word in sentence_lower for word in ["juego", "jugar", "juguemos"]):
        game_response = start_game()
        return [{'word': game_response['text'], 'pictogram': game_response['pictogram']}]

    # Original sentence processing
    processed_sentence = []
    doc = nlp(sentence)
    for token in doc:
        if token.pos_ == "VERB":
            morph = token.morph.to_dict()
            person = morph.get("Person")
            if person == "1": pronoun = "yo"
            elif person == "2": pronoun = "tú"
            elif person == "3": pronoun = "él"
            else: pronoun = None
            if pronoun:
                pictogram = nlp_utils.find_pictogram(pronoun, nlp_utils.pictograms)
                processed_sentence.append({'word': pronoun, 'pictogram': pictogram['path'] if pictogram else None})
            pictogram = nlp_utils.find_pictogram(token.lemma_, nlp_utils.pictograms)
            processed_sentence.append({'word': token.lemma_, 'pictogram': pictogram['path'] if pictogram else None})
        else:
            pictogram = nlp_utils.find_pictogram(token.text, nlp_utils.pictograms)
            processed_sentence.append({'word': token.text, 'pictogram': pictogram['path'] if pictogram else None})
    return processed_sentence

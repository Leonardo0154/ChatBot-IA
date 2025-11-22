from src.model import nlp_utils
import spacy
import os
import random
import re

# Load the spaCy model
nlp = spacy.load("es_core_news_sm")

# Dictionary to hold game states for each user
user_game_states = {}

def _get_default_game_state():
    """Returns a new, default game state dictionary."""
    return {
        "in_progress": False,
        "correct_answer": None,
        "pictogram_path": None,
        "mode": None,  # "game" or "guided_session"
        "guided_session_words": [],
        "guided_session_step": 0,
        "failures": 0
    }

def _get_user_game_state(username: str):
    """Retrieves or creates a game state for a given user."""
    if username not in user_game_states:
        user_game_states[username] = _get_default_game_state()
    return user_game_states[username]

def clear_user_game_state(username: str):
    """Clears the game state for a specific user."""
    if username in user_game_states:
        del user_game_states[username]

def start_game(username: str, category=None):
    """Starts a new game for a specific user."""
    game_state = _get_user_game_state(username)
    
    pictogram_pool = nlp_utils.pictograms
    
    if category:
        pictogram_pool = [p for p in pictogram_pool if category in p.get('tags', [])]
    
    if not pictogram_pool:
        return {"text": f"No pictograms found for category '{category}'.", "pictogram": None}

    # Filter for pictograms that have keywords
    valid_pictograms = [p for p in pictogram_pool if p.get('keywords')]
    if not valid_pictograms:
        return {"text": f"No usable pictograms with keywords found for category '{category}'.", "pictogram": None}

    pictogram = random.choice(valid_pictograms)
    
    game_state["in_progress"] = True
    game_state["mode"] = "game"
    game_state["correct_answer"] = pictogram['keywords'][0]['keyword']
    game_state["pictogram_path"] = pictogram['path']
    
    return {
        "text": f"¡Adivina la palabra! (Categoría: {category or 'General'})",
        "pictogram": game_state["pictogram_path"]
    }

def start_guided_session(username: str, words: list):
    """Starts a guided session for a specific user."""
    game_state = _get_user_game_state(username)
    
    game_state["in_progress"] = True
    game_state["mode"] = "guided_session"
    game_state["guided_session_words"] = words
    game_state["guided_session_step"] = 0
    
    first_word = words[0]
    pictogram = nlp_utils.find_pictogram(first_word, nlp_utils.pictograms)
    game_state["correct_answer"] = first_word
    game_state["pictogram_path"] = pictogram['path'] if pictogram else None

def process_sentence(username: str, sentence: str):
    """Processes a sentence for a given user, handles game logic, and maps words to pictograms."""
    game_state = _get_user_game_state(username)
    sentence_lower = sentence.lower()

    # Predefined conversational Q&A
    qa_pairs = {
        "what is your name?": "My name is ChatBot-IA.",
        "how are you?": "I'm doing great, thanks for asking!",
        "what can you do?": "I can help you communicate with pictograms, play games, and learn new things!",
        "hello": "Hello there!",
        "goodbye": "Goodbye! See you next time."
    }
    if sentence_lower in qa_pairs:
        return [{'word': qa_pairs[sentence_lower], 'pictogram': None}]

    if game_state["in_progress"]:
        if game_state["mode"] == "game":
            if sentence_lower == game_state["correct_answer"].lower():
                response_text = f"¡Correcto! La palabra es {game_state['correct_answer']}."
                clear_user_game_state(username) # Reset state after game ends
                return [{'word': response_text, 'pictogram': None}]
            else:
                game_state["failures"] += 1
                clue = game_state["correct_answer"][:1 + game_state["failures"]]
                return [{'word': f"Inténtalo de nuevo. La palabra empieza por '{clue.upper()}'.", 'pictogram': game_state["pictogram_path"]}]
        
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
                    clear_user_game_state(username) # Reset state after session ends
                    return [{'word': "¡Felicidades! Has completado la sesión.", 'pictogram': None}]
            else:
                game_state["failures"] += 1
                clue = game_state["correct_answer"][:1 + game_state["failures"]]
                return [{'word': f"Inténtalo de nuevo. La palabra empieza por '{clue.upper()}'.", 'pictogram': game_state["pictogram_path"]}]

    game_match = re.match(r"jugar a (.+)", sentence_lower)
    if game_match:
        category = game_match.group(1).strip()
        game_response = start_game(username, category)
        return [{'word': game_response['text'], 'pictogram': game_response['pictogram']}]
    elif any(word in sentence_lower.split() for word in ["juego", "jugar", "juguemos"]):
        game_response = start_game(username)
        return [{'word': game_response['text'], 'pictogram': game_response['pictogram']}]

    processed_sentence = []
    doc = nlp(sentence)
    for token in doc:
        # If the token is a verb, get its person and add the pronoun
        if token.pos_ == "VERB":
            morph = token.morph.to_dict()
            person = morph.get("Person")
            if person == "1":
                pronoun = "yo"
            elif person == "2":
                pronoun = "tú"
            elif person == "3":
                pronoun = "él" # or ella, or ello
            else:
                pronoun = None
            
            if pronoun:
                pictogram = nlp_utils.find_pictogram(pronoun, nlp_utils.pictograms)
                processed_sentence.append({
                    'word': pronoun,
                    'pictogram': pictogram['path'] if pictogram else None
                })

            pictogram = nlp_utils.find_pictogram(token.lemma_, nlp_utils.pictograms)
            processed_sentence.append({
                'word': token.lemma_,
                'pictogram': pictogram['path'] if pictogram else None
            })

        else:
            pictogram = nlp_utils.find_pictogram(token.text, nlp_utils.pictograms)
            processed_sentence.append({
                'word': token.text,
                'pictogram': pictogram['path'] if pictogram else None
            })
    return processed_sentence

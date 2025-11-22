from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from src.model import nlp_utils
import spacy
import os
import random
import re

# Load the spaCy model
nlp = spacy.load("es_core_news_sm")

class Chatbot:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("mrm8488/spanish-t5-small-sqac-for-qa")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("mrm8488/spanish-t5-small-sqac-for-qa")
        self.user_game_states = {}

    def _get_default_game_state(self):
        """Returns a new, default game state dictionary."""
        return {
            "in_progress": False,
            "correct_answer": None,
            "pictogram_path": None,
            "mode": None,
            "guided_session_words": [],
            "guided_session_step": 0,
            "failures": 0
        }

    def _get_user_game_state(self, username: str):
        """Retrieves or creates a game state for a given user."""
        if username not in self.user_game_states:
            self.user_game_states[username] = self._get_default_game_state()
        return self.user_game_states[username]

    def clear_user_game_state(self, username: str):
        """Clears the game state for a specific user."""
        if username in self.user_game_states:
            del self.user_game_states[username]

    def start_game(self, username: str, category=None):
        """Starts a new game for a specific user."""
        game_state = self._get_user_game_state(username)
        pictogram_pool = nlp_utils.pictograms
        if category:
            pictogram_pool = [p for p in pictogram_pool if category in p.get('tags', [])]
        if not pictogram_pool:
            return {"text": f"No pictograms found for category '{category}'.", "pictogram": None}
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
        
    def start_guided_session(self, username: str, words: list):
        """Starts a guided session for a specific user."""
        game_state = self._get_user_game_state(username)
        
        game_state["in_progress"] = True
        game_state["mode"] = "guided_session"
        game_state["guided_session_words"] = words
        game_state["guided_session_step"] = 0
        
        first_word = words[0]
        pictogram = nlp_utils.find_pictogram(first_word, nlp_utils.pictograms)
        game_state["correct_answer"] = first_word
        game_state["pictogram_path"] = pictogram['path'] if pictogram else None

    def process_sentence(self, username: str, sentence: str):
        """
        Processes a sentence for a given user, handles game logic, and generates a response.
        """
        game_state = self._get_user_game_state(username)
        sentence_lower = sentence.lower()

        if game_state["in_progress"]:
            if game_state["mode"] == "game":
                if sentence_lower == game_state["correct_answer"].lower():
                    response_text = f"¡Correcto! La palabra es {game_state['correct_answer']}."
                    self.clear_user_game_state(username)
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
                        self.clear_user_game_state(username)
                        return [{'word': "¡Felicidades! Has completado la sesión.", 'pictogram': None}]
                else:
                    game_state["failures"] += 1
                    clue = game_state["correct_answer"][:1 + game_state["failures"]]
                    return [{'word': f"Inténtalo de nuevo. La palabra empieza por '{clue.upper()}'.", 'pictogram': game_state["pictogram_path"]}]
        else:
            game_match = re.match(r"jugar a (.+)", sentence_lower)
            if game_match:
                category = game_match.group(1).strip()
                game_response = self.start_game(username, category)
                return [{'word': game_response['text'], 'pictogram': game_response['pictogram']}]
            elif any(word in sentence_lower.split() for word in ["juego", "jugar", "juguemos"]):
                game_response = self.start_game(username)
                return [{'word': game_response['text'], 'pictogram': game_response['pictogram']}]

            # Use the T5 model to generate a response
            input_text = f"question: {sentence}"
            inputs = self.tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
            outputs = self.model.generate(inputs, max_length=150, num_beams=4, early_stopping=True)
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # "Smart" pictogram integration
            processed_response = []
            doc = nlp(response_text)
            for token in doc:
                if token.pos_ in ["NOUN", "VERB"]:
                    pictogram = nlp_utils.find_pictogram(token.text, nlp_utils.pictograms)
                    processed_response.append({'word': token.text, 'pictogram': pictogram['path'] if pictogram else None})
                else:
                    processed_response.append({'word': token.text, 'pictogram': None})
            
            return processed_response

# Instantiate the chatbot
chatbot = Chatbot()


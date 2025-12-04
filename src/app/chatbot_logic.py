from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from src.model import nlp_utils, intent_classifier, emotion_classifier
from src.app import data_manager, consent_manager
from unidecode import unidecode
import spacy
import random
import re
from collections import Counter

# Load the spaCy model
nlp = spacy.load("es_core_news_sm")
DEFAULT_PROMPT_PREFIX = "Eres un tutor de comunicación aumentativa que responde en español claro y breve."
DEFAULT_FALLBACK = "No encontré una respuesta específica, pero podemos seguir practicando tus pictogramas."

class Chatbot:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("mrm8488/spanish-t5-small-sqac-for-qa")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("mrm8488/spanish-t5-small-sqac-for-qa")
        self.user_game_states = {}
        self.support_content = data_manager.load_support_content()

    def reload_support_content(self):
        """Reload support packs when teachers update curated content."""
        self.support_content = data_manager.load_support_content()

    def _get_default_game_state(self):
        """Returns a new, default game state dictionary."""
        return {
            "in_progress": False,
            "correct_answer": None,
            "pictogram_path": None,
            "mode": None,
            "guided_session_words": [],
            "guided_session_step": 0,
            "failures": 0,
            "assignment_metadata": None,
            "use_scripted": False
        }

    def _get_user_game_state(self, username: str):
        """Retrieves or creates a game state for a given user."""
        if username not in self.user_game_states:
            self.user_game_states[username] = self._get_default_game_state()
        return self.user_game_states[username]

    def _wrap_text_with_pictograms(self, text: str, forced_pictogram: str | None = None):
        doc = nlp(text)
        response = []
        for token in doc:
            if not token.text.strip():
                continue
            pictogram_path = forced_pictogram
            if forced_pictogram is None and token.pos_ in ["NOUN", "VERB"]:
                pictogram = nlp_utils.find_pictogram(token.text, nlp_utils.pictograms)
                pictogram_path = pictogram['path'] if pictogram else None
            response.append({'word': token.text, 'pictogram': pictogram_path})
        return response or [{'word': text, 'pictogram': forced_pictogram}]

    def _single_entry_response(self, text: str, pictogram_path: str | None = None):
        """Helper for deterministic responses without token splitting."""
        return [{'word': text, 'pictogram': pictogram_path}]

    def _build_progress_context(self, username: str):
        summary = data_manager.get_user_progress_summary(username)
        sections = []
        if summary['total_interactions'] > 0:
            sections.append(f"Ha practicado {summary['total_interactions']} veces con el asistente.")
        if summary['most_common_words']:
            word, freq = summary['most_common_words'][0]
            sections.append(f"La palabra '{word}' apareció {freq} veces en sus ejercicios.")
        if summary['last_interaction']:
            sections.append(f"Última práctica registrada: {summary['last_interaction']}.")
        return " ".join(sections).strip()

    def _build_assignment_context(self, game_state: dict):
        metadata = game_state.get('assignment_metadata') or {}
        sections = []
        assignment_support = self.support_content.get('assignment', {})
        if metadata.get('task'):
            template = random.choice(assignment_support.get('intro_templates', [])) if assignment_support.get('intro_templates') else None
            text = template.format(task=metadata['task'], words=", ".join(metadata.get('target_words', []))) if template else f"Objetivo actual: {metadata['task']}."
            sections.append(text)
        elif metadata.get('target_words'):
            sections.append(f"Objetivo actual: practicar {', '.join(metadata['target_words'])}.")
        return " ".join(sections).strip()

    def _compose_transformer_input(self, username: str, sentence: str, role: str):
        game_state = self._get_user_game_state(username)
        progress_text = self._build_progress_context(username)
        assignment_text = self._build_assignment_context(game_state)
        context_hint = self.support_content.get('general', {}).get('context_hint')
        context_sections = [assignment_text, progress_text, context_hint]
        context = " ".join([sec for sec in context_sections if sec])
        prompt_prefix = self.support_content.get('general', {}).get('prompt_prefix', DEFAULT_PROMPT_PREFIX)
        if context:
            return f"{prompt_prefix} Contexto: {context} Pregunta: {sentence}"
        return f"{prompt_prefix} Pregunta: {sentence}"

    def _detect_intent_emotion(self, sentence: str):
        if not sentence:
            return ('otra_consulta', 0.0), ('neutral', 0.0)
        intent = intent_classifier.predict_intent(sentence)
        emotion = emotion_classifier.predict_emotion(sentence)
        return intent, emotion

    def _maybe_scripted_response(self, username: str, sentence_lower: str, role: str):
        general_support = self.support_content.get('general', {})
        for trigger in general_support.get('greeting_triggers', []):
            if trigger in sentence_lower:
                greeting = random.choice(general_support.get('greetings', [general_support.get('fallback', DEFAULT_FALLBACK)]))
                return self._single_entry_response(greeting)

        game_state = self._get_user_game_state(username)
        metadata = game_state.get('assignment_metadata')
        if metadata and role in ['child', 'student']:
            assignment_support = self.support_content.get(metadata.get('type', 'assignment'), {})
            template_list = assignment_support.get('intro_templates') or assignment_support.get('success')
            if template_list:
                text = random.choice(template_list)
                words = metadata.get('target_words') or []
                formatted = text.format(
                    task=metadata.get('task', 'practicar palabras'),
                    words=', '.join(words),
                    word=words[0] if words else ''
                )
                pictogram_path = None
                if words:
                    pictogram = nlp_utils.find_pictogram(words[0], nlp_utils.pictograms)
                    pictogram_path = pictogram['path'] if pictogram else None
                return self._single_entry_response(formatted, pictogram_path)
        return None

    def _generate_dynamic_steps(self, scenario: dict, sentence: str, emotion_label: str):
        prompt = (
            "Eres un tutor AAC. "
            f"Escenario: {scenario.get('id', 'rutina')}. "
            f"Tono: {emotion_label}. "
            "Genera exactamente tres pasos cortos en español para ayudar al niño. "
            f"Consulta: {sentence}. "
            "Separa los pasos con ' || '."
        )
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=256, truncation=True)
            outputs = self.model.generate(inputs, max_length=150, num_beams=4, early_stopping=True)
            decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception:
            return scenario.get('steps') or []
        parts = [segment.strip(" -:\n") for segment in decoded.split('||') if segment.strip()]
        return parts or scenario.get('steps') or []

    def _summarize_recent_practice(self, username: str):
        logs = data_manager.get_recent_interactions(username, limit=25)
        if not logs:
            return ""
        words = []
        for entry in logs:
            for token in entry.get('processed_sentence', []):
                word = (token or {}).get('word')
                if not word:
                    continue
                cleaned = word.strip().lower()
                if len(cleaned) <= 5 and cleaned.isalpha():
                    words.append(cleaned)
        if not words:
            return ""
        most_common = [w for w, _ in Counter(words).most_common(3)]
        if not most_common:
            return ""
        formatted = ", ".join(most_common)
        return f"Ya practicamos sonidos como: {formatted}."

    def _scenario_template_response(self, username: str, sentence: str, sentence_lower: str, intent_label: str, emotion_label: str):
        scenarios = self.support_content.get('scenarios', [])
        if not isinstance(scenarios, list):
            return None

        for entry in scenarios:
            triggers = entry.get('triggers') or []
            intents = entry.get('intents') or []
            matches_intent = intent_label in intents if intents else False
            matches_trigger = any(trigger in sentence_lower for trigger in triggers if trigger)
            if not (matches_intent or matches_trigger):
                continue

            steps = entry.get('steps') or []
            if entry.get('dynamic_steps'):
                steps = self._generate_dynamic_steps(entry, sentence, emotion_label)

            text_parts = [entry.get('response')]
            if entry.get('id') == 'terapia_practicar_sonido':
                summary = self._summarize_recent_practice(username)
                if summary:
                    text_parts.append(summary)
            if steps:
                ordered = " ".join(f"{idx + 1}. {step}" for idx, step in enumerate(steps))
                text_parts.append(ordered)
            if entry.get('follow_up'):
                text_parts.append(entry['follow_up'])
            text = " ".join(part.strip() for part in text_parts if part).strip()
            pictogram_path = None
            keyword = entry.get('pictogram_keyword')
            if keyword:
                pictogram = nlp_utils.find_pictogram(keyword, nlp_utils.pictograms)
                pictogram_path = pictogram['path'] if pictogram else None
            if text:
                return self._single_entry_response(text, pictogram_path)
        return None

    def _related_vocab_response(self, sentence: str):
        """Returns a deterministic hint tying the word to related vocabulary."""
        related_map = self.support_content.get('related_vocab', {})
        if not related_map:
            return None

        general_support = self.support_content.get('general', {})
        templates = general_support.get('related_templates', [])
        fallback_template = "Cuando dices {word}, también recuerda {associations}."

        tokens = re.findall(r"[\wáéíóúñü]+", sentence.lower())
        guessed = self._semantic_card_match(sentence.lower())
        if guessed:
            tokens.insert(0, guessed)
        for token in tokens:
            normalized = unidecode(token)
            associations = related_map.get(normalized)
            pictogram = nlp_utils.find_pictogram(token, nlp_utils.pictograms)
            if not associations and pictogram:
                associations = [kw.get('keyword') for kw in pictogram.get('keywords', []) if kw.get('keyword') and kw.get('keyword').lower() != token]
            if not associations:
                continue

            assoc_text = ", ".join(associations[:3])
            template = random.choice(templates) if templates else fallback_template
            text = template.format(word=token, associations=assoc_text)
            pictogram_path = pictogram['path'] if pictogram else None
            return self._single_entry_response(text, pictogram_path)
        return None

    def _semantic_card_match(self, sentence_lower: str):
        related_map = self.support_content.get('related_vocab', {})
        if not related_map:
            return None
        tokens = set(re.findall(r"[\wáéíóúñü]+", sentence_lower))
        tokens_unidecode = {unidecode(t) for t in tokens}
        for main_word, associations in related_map.items():
            for assoc in associations:
                if unidecode(assoc.lower()) in tokens_unidecode:
                    return main_word
        return None

    def _emotion_support_response(self, emotion_label: str):
        responses = {
            'triste': "Siento que estés triste. Respira conmigo y elige el pictograma de abrazo si quieres contarme más.",
            'ansioso': "Cuando algo preocupa, respiramos lento y nombramos lo que vemos. Estoy contigo.",
            'enojado': "Está bien estar enojado. Sacude tus manos y cuenta hasta cinco antes de seguir.",
            'orgulloso': "¡Qué orgullo! Guarda ese sentimiento tocando el pictograma de trofeo.",
            'calmo': "Qué bueno sentir calma. Podemos seguir a tu ritmo.",
            'neutral': "Gracias por contarme. Seguimos juntos."
        }
        return self._single_entry_response(responses.get(emotion_label, responses['neutral']))

    def _extract_permission_action(self, sentence_lower: str):
        match = re.search(r"(?:puedo|me dejas|me permites|está bien si|esta bien si)(.+)", sentence_lower)
        if not match:
            return None
        action = match.group(1).strip()
        return action or None

    def _consent_response(self, username: str, sentence: str, sentence_lower: str):
        action = self._extract_permission_action(sentence_lower)
        consent_manager.log_audit('chatbot_consent_request', username, metadata={'text': sentence})
        if action:
            text = f"Sí, avisemos a tu adulto. Puedes {action} y marca el pictograma de pausa cuando regreses."
        else:
            text = "Gracias por avisar. Anoto tu solicitud y esperamos confirmación del adulto."
        return self._single_entry_response(text)

    def _factual_response(self, sentence: str):
        prompt = (
            "Responde en español latino con máximo 25 palabras. "
            "Da una explicación simple para niños y sugiere un pictograma si aplica. "
            f"Pregunta: {sentence}"
        )
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=256, truncation=True)
            outputs = self.model.generate(inputs, max_length=80, num_beams=4, early_stopping=True)
            text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception:
            text = self.support_content.get('general', {}).get('fallback', DEFAULT_FALLBACK)
        return self._wrap_text_with_pictograms(text)

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
        game_state["assignment_metadata"] = {
            "type": "game",
            "task": f"Adivinar palabras de la categoría {category or 'general'}",
            "target_words": [game_state["correct_answer"]]
        }
        game_state["use_scripted"] = True
        return {
            "text": f"¡Adivina la palabra! (Categoría: {category or 'General'})",
            "pictogram": game_state["pictogram_path"]
        }
        
    def start_guided_session(self, username: str, words: list, metadata: dict | None = None):
        """Starts a guided session for a specific user."""
        if not words:
            return

        game_state = self._get_user_game_state(username)
        game_state["in_progress"] = True
        game_state["mode"] = "guided_session"
        game_state["guided_session_words"] = words
        game_state["guided_session_step"] = 0
        game_state["assignment_metadata"] = {
            "type": (metadata or {}).get('type', 'guided_session'),
            "task": (metadata or {}).get('task', 'Sesión guiada de palabras'),
            "title": (metadata or {}).get('title'),
            "target_words": words
        }
        game_state["use_scripted"] = True

        first_word = words[0]
        pictogram = nlp_utils.find_pictogram(first_word, nlp_utils.pictograms)
        game_state["correct_answer"] = first_word
        game_state["pictogram_path"] = pictogram['path'] if pictogram else None

    def process_sentence(self, username: str, sentence: str, role: str | None = None):
        """
        Processes a sentence for a given user, handles game logic, and generates a response.
        """
        game_state = self._get_user_game_state(username)
        sentence_lower = sentence.lower()
        role = role or 'student'
        intent_info, emotion_info = self._detect_intent_emotion(sentence)
        intent_label, _ = intent_info
        emotion_label, _ = emotion_info

        if game_state["in_progress"]:
            if game_state["mode"] == "game":
                semantic_guess = self._semantic_card_match(sentence_lower)
                correct = game_state["correct_answer"].lower()
                if sentence_lower == correct or (semantic_guess and semantic_guess.lower() == correct):
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
                        success_text = random.choice(self.support_content.get('guided_session', {}).get('success', ["¡Muy bien!"])).format(word=next_word)
                        return self._single_entry_response(success_text, game_state["pictogram_path"])
                    else:
                        self.clear_user_game_state(username)
                        guided_success = self.support_content.get('guided_session', {}).get('success', [])
                        farewell = random.choice(guided_success).format(word="") if guided_success else "¡Felicidades! Has completado la sesión."
                        return self._single_entry_response(farewell)
                else:
                    game_state["failures"] += 1
                    clue = game_state["correct_answer"][:1 + game_state["failures"]]
                    hint_template = self.support_content.get('guided_session', {}).get('hint', "La palabra comienza con {clue}")
                    hint_text = hint_template.format(clue=clue.upper())
                    return self._single_entry_response(hint_text, game_state["pictogram_path"])
        else:
            game_match = re.match(r"jugar a (.+)", sentence_lower)
            if game_match:
                category = game_match.group(1).strip()
                game_response = self.start_game(username, category)
                return self._single_entry_response(game_response['text'], game_response['pictogram'])
            elif any(word in sentence_lower.split() for word in ["juego", "jugar", "juguemos"]):
                game_response = self.start_game(username)
                return self._single_entry_response(game_response['text'], game_response['pictogram'])
            scripted = self._maybe_scripted_response(username, sentence_lower, role)
            if scripted:
                return scripted

            scenario_match = self._scenario_template_response(username, sentence, sentence_lower, intent_label, emotion_label)
            if scenario_match:
                return scenario_match

            if intent_label == 'juego_pista':
                guess = self._semantic_card_match(sentence_lower)
                if guess:
                    pictogram = nlp_utils.find_pictogram(guess, nlp_utils.pictograms)
                    text = f"Creo que piensas en {guess}. Busca ese pictograma y dime si coincide."
                    return self._single_entry_response(text, pictogram['path'] if pictogram else None)

            if intent_label == 'consentimiento':
                return self._consent_response(username, sentence, sentence_lower)

            if intent_label == 'emocional_checkin':
                return self._emotion_support_response(emotion_label)

            if intent_label == 'factual_pregunta':
                return self._factual_response(sentence)

            related = self._related_vocab_response(sentence)
            if related:
                return related

            input_text = self._compose_transformer_input(username, sentence, role)
            try:
                inputs = self.tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
                outputs = self.model.generate(inputs, max_length=150, num_beams=4, early_stopping=True)
                response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception:
                fallback_text = self.support_content.get('general', {}).get('fallback', DEFAULT_FALLBACK)
                return self._wrap_text_with_pictograms(fallback_text)

            if len(response_text.split()) < 3:
                fallback_text = self.support_content.get('general', {}).get('fallback', DEFAULT_FALLBACK)
                return self._wrap_text_with_pictograms(fallback_text)

            return self._wrap_text_with_pictograms(response_text)

# Instantiate the chatbot
chatbot = Chatbot()


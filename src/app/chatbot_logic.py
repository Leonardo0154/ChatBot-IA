from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from src.model import nlp_utils, intent_classifier, emotion_classifier
from src.app import data_manager, consent_manager
from unidecode import unidecode
import spacy
import random
import re
from collections import Counter
import os

# Load the spaCy model
nlp = spacy.load("es_core_news_sm")
DEFAULT_PROMPT_PREFIX = "Eres un tutor de comunicación aumentativa que responde en español claro y breve."
DEFAULT_FALLBACK = "No encontré una respuesta específica, pero podemos seguir practicando tus pictogramas."
EMOTION_KEYWORDS = {
    'triste': 'triste',
    'asustado': 'miedo',
    'miedo': 'miedo',
    'enojado': 'enojado',
    'molesto': 'enojado',
    'ansioso': 'ansioso',
    'nervioso': 'ansioso',
    'cansado': 'cansado',
    'aburrido': 'cansado',
    'feliz': 'orgulloso',
    'contento': 'orgulloso'
}

class Chatbot:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("mrm8488/spanish-t5-small-sqac-for-qa")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("mrm8488/spanish-t5-small-sqac-for-qa")
        self.user_game_states = {}
        # Canonical categories mapped to synonyms for loose matching.
        self.category_synonyms = {
            'animal': ['animal', 'animales', 'fauna', 'mascota'],
            'comida': ['comida', 'alimento', 'comer', 'comidas', 'fruta', 'verdura'],
            'transporte': ['transporte', 'vehiculo', 'vehículo', 'auto', 'carro', 'bus', 'camion'],
            'escuela': ['escuela', 'clase', 'colegio', 'estudio'],
            'hogar': ['casa', 'hogar', 'familia', 'cocina', 'cuarto']
        }

    def _infer_category(self, sentence_lower: str) -> str | None:
        for canon, terms in self.category_synonyms.items():
            if any(term in sentence_lower for term in terms):
                return canon
        return None


    def _normalize_text(self, text: str):
        cleaned = unidecode(re.sub(r"[^a-z0-9áéíóúñü\s]", " ", text.lower()))
        return [t for t in cleaned.split() if t]

    def _is_parroting(self, question: str, answer: str) -> bool:
        if not answer:
            return True
        ans_tokens = self._normalize_text(answer)
        if not ans_tokens or len(ans_tokens) <= 4:
            return True
        question_tokens = set(self._normalize_text(question))
        overlap = sum(1 for t in ans_tokens if t in question_tokens)
        return (overlap / len(ans_tokens)) >= 0.7

    def reload_support_content(self):
        """Legacy no-op kept for compatibility when support packs were curated."""
        return

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
            "use_scripted": False,
            "drill_items": [],
            "drill_round": 0,
            "drill_target": None,
            "category": None
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

    def _describe_with_pictogram(self, sentence: str):
        """Builds a short descriptive sentence from pictogram metadata when available."""
        tokens = re.findall(r"[\wáéíóúñü]+", sentence.lower())
        skip = {"como", "qué", "que", "un", "una", "el", "la", "es", "soy", "estoy", "palabra", "veces"}
        for token in tokens:
            if token in skip:
                continue
            pictogram = nlp_utils.find_pictogram(token, nlp_utils.pictograms)
            if not pictogram:
                continue
            keywords = [kw.get('keyword') for kw in pictogram.get('keywords', []) if kw.get('keyword')]
            focus = list(dict.fromkeys(keywords))[:3]
            if not focus:
                continue
            text = f"{token.capitalize()} se relaciona con {', '.join(focus)}. Dime cuál ves en tu pictograma."
            return self._single_entry_response(text, pictogram.get('path'))
        return None

    def _is_skip_request(self, sentence_lower: str) -> bool:
        triggers = ["otro", "otra", "siguiente", "cambia", "muy dificil", "muy difícil", "no se", "no sé", "skip", "next"]
        return any(t in sentence_lower for t in triggers)

    def _valid_pictogram(self, pictogram: dict) -> bool:
        if not pictogram or not pictogram.get('path'):
            return False
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/raw/ARASAAC_ES'))
        return os.path.exists(os.path.join(base, pictogram['path']))

    def _has_digits(self, text: str) -> bool:
        return bool(re.search(r"\d", text))

    def _maybe_digit_response(self, sentence: str, intent_info, emotion_info, suggested_pictograms, entities):
        digits = re.findall(r"\d+", sentence)
        if not digits:
            return None
        number_str = digits[0]
        text = f"Veo el número {number_str}. Dime qué palabra o pictograma quieres practicar con ese número."
        return self._package_response(self._single_entry_response(text), intent_info, emotion_info, suggested_pictograms, entities)

    def _matches_category(self, pictogram: dict, category: str | None) -> bool:
        if not category:
            return True
        tags = [t.lower() for t in pictogram.get('tags', []) if t]
        keywords = [(kw.get('keyword') or '').lower() for kw in pictogram.get('keywords', [])]
        synonyms = self.category_synonyms.get(category, [category])
        for syn in synonyms:
            if any(syn in t for t in tags + keywords):
                return True
        return False

    def _start_drill(self, username: str, top_k: int = 3, category: str | None = None):
        game_state = self._get_user_game_state(username)
        # Sample pictograms with keywords, short alphabetical keywords, and valid assets.
        candidates = []
        for p in nlp_utils.pictograms:
            if not self._valid_pictogram(p):
                continue
            kws = [kw.get('keyword') for kw in p.get('keywords', []) if kw.get('keyword')]
            if not kws:
                continue
            main_kw = kws[0]
            if not re.fullmatch(r"[A-Za-záéíóúñüÁÉÍÓÚÑÜ]+", main_kw) or len(main_kw) > 10:
                continue
            if self._matches_category(p, category):
                candidates.append(p)
        if len(candidates) < 3:
            # Fallback to general pool if category is too narrow.
            fallback_items = [p for p in nlp_utils.pictograms if self._valid_pictogram(p)]
            if len(fallback_items) >= 3:
                candidates = fallback_items
            else:
                msg = "No encontré suficientes pictos. Prueba otra categoría o di solo 'practicar pictos'."
                return self._single_entry_response(msg)
        items = random.sample(candidates, k=min(top_k, len(candidates)))
        game_state["drill_items"] = items
        game_state["drill_round"] = 0
        target = (items[0].get('keywords') or [{}])[0].get('keyword') or ""
        game_state["drill_target"] = target
        game_state["in_progress"] = True
        game_state["mode"] = "drill"
        # Build a pictogram-first prompt: instruction + option pictos
        options = []
        for pic in items:
            kw = (pic.get('keywords') or [{}])[0].get('keyword', '')
            options.append({'word': kw or '', 'pictogram': pic.get('path')})
        return [{'word': f"Toca o di: {target}.", 'pictogram': items[0].get('path')}] + options

    def _drill_next_round(self, username: str, previous_items: list):
        game_state = self._get_user_game_state(username)
        candidates = []
        prev_paths = {p.get('path') for p in previous_items if isinstance(p, dict) and p.get('path')}
        for p in nlp_utils.pictograms:
            if p.get('path') in prev_paths:
                continue
            if not self._valid_pictogram(p):
                continue
            kws = [kw.get('keyword') for kw in p.get('keywords', []) if kw.get('keyword')]
            if not kws:
                continue
            main_kw = kws[0]
            if not re.fullmatch(r"[A-Za-záéíóúñüÁÉÍÓÚÑÜ]+", main_kw) or len(main_kw) > 10:
                continue
            candidates.append(p)
        if not candidates:
            candidates = [p for p in nlp_utils.pictograms if p.get('keywords') and self._valid_pictogram(p)]
        items = random.sample(candidates, k=min(3, len(candidates)))
        game_state["drill_items"] = items
        game_state["drill_round"] += 1
        target = (items[0].get('keywords') or [{}])[0].get('keyword') or ""
        game_state["drill_target"] = target
        options = []
        for pic in items:
            kw = (pic.get('keywords') or [{}])[0].get('keyword', '')
            options.append({'word': kw or '', 'pictogram': pic.get('path')})
        return [{'word': f"Ahora di o toca: {target}.", 'pictogram': items[0].get('path')}] + options

    def _choice_prompt(self, suggested_pictograms):
        if not suggested_pictograms:
            return None
        top = suggested_pictograms[:2]
        names = [p.get('keyword') for p in top if p.get('keyword')]
        if len(names) < 2:
            return None
        text = f"¿Quieres practicar {names[0]} o {names[1]}? Elige uno para empezar."
        pictogram_path = top[0].get('path') if top[0].get('path') else None
        return self._single_entry_response(text, pictogram_path)

    def _package_response(self, processed_sentence, intent_info, emotion_info, suggested_pictograms=None, entities=None):
        intent_label, intent_score = intent_info
        emotion_label, emotion_score = emotion_info
        # Defensive dedupe to avoid duplicated items in FE
        seen_proc = set()
        cleaned_proc = []
        for item in processed_sentence or []:
            key = f"{item.get('word')}|{item.get('pictogram')}"
            if key in seen_proc:
                continue
            seen_proc.add(key)
            cleaned_proc.append(item)
        seen_sugg = set()
        cleaned_sugg = []
        for p in suggested_pictograms or []:
            key = p.get('path') or p.get('keyword')
            if key in seen_sugg:
                continue
            seen_sugg.add(key)
            cleaned_sugg.append(p)
        return {
            'processed_sentence': cleaned_proc,
            'intent': {'label': intent_label, 'score': intent_score},
            'emotion': {'label': emotion_label, 'score': emotion_score},
            'suggested_pictograms': cleaned_sugg,
            'entities': entities or []
        }

    def _suggest_pictograms(self, sentence: str, top_k: int = 5):
        try:
            raw = nlp_utils.suggest_pictograms(sentence, top_k=top_k)
            seen = set()
            deduped = []
            for p in raw:
                key = p.get('path') or p.get('keyword')
                if not key or key in seen:
                    continue
                seen.add(key)
                deduped.append(p)
            return deduped
        except Exception:
            return []

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
        if metadata.get('task'):
            sections.append(f"Objetivo actual: {metadata['task']}.")
        if metadata.get('target_words'):
            sections.append(f"Palabras objetivo: {', '.join(metadata['target_words'])}.")
        return " ".join(sections).strip()

    def _compose_transformer_input(self, username: str, sentence: str, role: str):
        game_state = self._get_user_game_state(username)
        progress_text = self._build_progress_context(username)
        assignment_text = self._build_assignment_context(game_state)
        context_sections = [assignment_text, progress_text]
        context = " ".join([sec for sec in context_sections if sec])
        prompt_prefix = DEFAULT_PROMPT_PREFIX
        if context:
            return f"{prompt_prefix} Contexto: {context} Pregunta: {sentence}"
        return f"{prompt_prefix} Pregunta: {sentence}"

    def _detect_intent_emotion(self, sentence: str):
        if not sentence:
            return ('otra_consulta', 0.0), ('neutral', 0.0)
        intent = intent_classifier.predict_intent(sentence)
        emotion = emotion_classifier.predict_emotion(sentence)
        return intent, emotion

    def _extract_entities(self, sentence: str):
        if not sentence:
            return []
        doc = nlp(sentence)
        return [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]

    def _maybe_scripted_response(self, username: str, sentence_lower: str, role: str):
        game_state = self._get_user_game_state(username)
        metadata = game_state.get('assignment_metadata')
        if metadata and role in ['child', 'student']:
            words = metadata.get('target_words') or []
            task = metadata.get('task', 'practicar palabras')
            prompt = (
                "Eres un tutor AAC. Genera un saludo breve y motivador en español "
                "para iniciar una actividad con un niño. Incluye la tarea y las palabras objetivo si existen. "
                f"Tarea: {task}. Palabras: {', '.join(words)}."
            )
            try:
                inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=256, truncation=True)
                outputs = self.model.generate(inputs, max_length=80, num_beams=4, early_stopping=True)
                text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception:
                text = f"Vamos a {task}." if task else "¡Vamos a practicar!"

            pictogram_path = None
            if words:
                pictogram = nlp_utils.find_pictogram(words[0], nlp_utils.pictograms)
                pictogram_path = pictogram['path'] if pictogram else None
            return self._single_entry_response(text, pictogram_path)
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
        return None

    def _related_vocab_response(self, sentence: str):
        tokens = [t for t in nlp(sentence) if t.pos_ in {"NOUN", "PROPN"}]
        if not tokens:
            return None
        focus = tokens[0].lemma_.lower()
        suggestions = self._suggest_pictograms(focus, top_k=4)
        if not suggestions:
            return self._single_entry_response("Puedo mostrar pictos si me dices la palabra a relacionar.")
        options = []
        for s in suggestions:
            options.append({'word': s.get('keyword') or focus, 'pictogram': s.get('path')})
        return [{'word': f"Practiquemos palabras relacionadas con {focus}:", 'pictogram': None}] + options

    def _sample_generic_pictos(self, n: int = 4):
        picks = []
        for p in nlp_utils.pictograms:
            if len(picks) >= n:
                break
            if self._valid_pictogram(p):
                kw = (p.get('keywords') or [{}])[0].get('keyword', '')
                picks.append({'word': kw, 'pictogram': p.get('path')})
        return picks

    def _semantic_card_match(self, sentence_lower: str):
        return None

    def _emotion_support_response(self, emotion_label: str):
        prompt = (
            "Eres un tutor AAC en español. En 18 palabras, valida la emoción y da 2 micro-acciones para regularse. "
            "Usa tono cálido y menciona un pictograma sugerido (respirar, abrazo, calma, trofeo). "
            f"Emoción: {emotion_label}."
        )
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=256, truncation=True)
            outputs = self.model.generate(inputs, max_length=70, num_beams=4, early_stopping=True)
            text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception:
            text = "Respira conmigo, toca calma o abrazo y dime cómo sigues."

        # Add a check-out question to close the loop with the child.
        text = f"{text} ¿Te sientes mejor o igual?"

        pictogram_path = None
        if emotion_label in ['triste', 'ansioso', 'enojado', 'miedo']:
            pictogram = nlp_utils.find_pictogram('calma', nlp_utils.pictograms) or nlp_utils.find_pictogram('respirar', nlp_utils.pictograms)
            pictogram_path = pictogram['path'] if pictogram else None
        elif emotion_label in ['orgulloso', 'feliz']:
            pictogram = nlp_utils.find_pictogram('trofeo', nlp_utils.pictograms)
            pictogram_path = pictogram['path'] if pictogram else None
        return self._single_entry_response(text, pictogram_path)

    def _extract_permission_action(self, sentence_lower: str):
        match = re.search(r"(?:puedo|me dejas|me permites|está bien si|esta bien si)(.+)", sentence_lower)
        if not match:
            return None
        action = match.group(1).strip()
        return action or None

    def _consent_response(self, username: str, sentence: str, sentence_lower: str):
        action = self._extract_permission_action(sentence_lower)
        consent_manager.log_audit('chatbot_consent_request', username, metadata={'text': sentence})
        prompt = (
            "Eres un tutor AAC en español. Responde en 18 palabras. "
            "1) Agradece y confirma que avisarás al adulto. 2) Pide esperar con pictograma de pausa. 3) Repite la acción pedida. "
            f"Petición: {action or sentence}."
        )
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=256, truncation=True)
            outputs = self.model.generate(inputs, max_length=70, num_beams=4, early_stopping=True)
            text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception:
            text = "Aviso al adulto, usa pausa y esperamos juntos."

        pictogram = nlp_utils.find_pictogram('pausa', nlp_utils.pictograms) or nlp_utils.find_pictogram('esperar', nlp_utils.pictograms)
        pictogram_path = pictogram['path'] if pictogram else None
        return self._single_entry_response(text, pictogram_path)

    def _factual_response(self, sentence: str):
        text = (
            "Por ahora no doy respuestas de ciencia o datos. "
            "Puedo ayudarte a practicar pictogramas, jugar, expresar emociones o pedir ayuda." 
            "Dime qué quieres practicar."
        )
        return self._single_entry_response(text)

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
        game_state["category"] = category
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
        intent_label, intent_score = intent_info
        emotion_label, _ = emotion_info

        # Upgrade to emotional check-in when emotion keywords are present, even if intent is low-confidence.
        for keyword, mapped in EMOTION_KEYWORDS.items():
            if keyword in sentence_lower:
                intent_label = 'emocional_checkin'
                intent_info = (intent_label, max(intent_score, 0.51))
                emotion_label = mapped
                emotion_info = (emotion_label, 0.7)
                break

        # Treat "por qué/por que/porque" questions as factual to avoid parroting.
        if re.search(r"\bpor que\b|\bpor qué\b|^porque\b", sentence_lower):
            intent_label = 'factual_pregunta'
            intent_info = (intent_label, max(intent_score, 0.65))

        # Health/pain quick support
        if any(word in sentence_lower for word in ["duele", "dolor", "barriga", "panza", "estomago", "estómago"]):
            pictogram = nlp_utils.find_pictogram('doctor', nlp_utils.pictograms) or nlp_utils.find_pictogram('ayuda', nlp_utils.pictograms)
            pictogram_path = pictogram['path'] if pictogram and self._valid_pictogram(pictogram) else None
            text = "Siento que te duele. Respira 3 veces, toca ayuda/médico y avisa a tu adulto." 
            return self._package_response(self._single_entry_response(text, pictogram_path), ('salud', 0.7), emotion_info, suggested_pictograms=self._suggest_pictograms(sentence), entities=self._extract_entities(sentence))

        # If intent confidence is low, fall back to open-ended generation to avoid misroutes.
        if intent_score < 0.5:
            intent_label = 'otra_consulta'
            intent_info = (intent_label, intent_score)
        suggested_pictograms = self._suggest_pictograms(sentence)
        entities = self._extract_entities(sentence)

        if game_state["in_progress"]:
            # Allow user to skip/advance when the current card feels difícil
            if self._is_skip_request(sentence_lower):
                prev_category = game_state.get("category")
                skip_entity = {
                    'label': 'skip',
                    'text': sentence,
                    'mode': game_state.get('mode'),
                    'pictogram': game_state.get('pictogram_path')
                }
                # Start a fresh card, preserving category when available
                self.clear_user_game_state(username)
                new_game = self.start_game(username, prev_category)
                skip_text = "Marcado como difícil. Cambiamos de pictograma." if prev_category else "Cambiamos de pictograma."
                combined = f"{skip_text} {new_game['text']}"
                return self._package_response(
                    self._single_entry_response(combined, new_game.get('pictogram')),
                    intent_info,
                    emotion_info,
                    suggested_pictograms,
                    entities=[skip_entity]
                )
            if game_state["mode"] == "game":
                semantic_guess = self._semantic_card_match(sentence_lower)
                correct = game_state["correct_answer"].lower()
                if sentence_lower == correct or (semantic_guess and semantic_guess.lower() == correct):
                    response_text = f"¡Correcto! La palabra es {game_state['correct_answer']}."
                    self.clear_user_game_state(username)
                    return self._package_response(self._single_entry_response(response_text), intent_info, emotion_info, suggested_pictograms, entities)
                else:
                    game_state["failures"] += 1
                    clue = game_state["correct_answer"][:1 + game_state["failures"]]
                    return self._package_response(
                        [{'word': f"Inténtalo de nuevo. La palabra empieza por '{clue.upper()}'.", 'pictogram': game_state["pictogram_path"]}],
                        intent_info,
                        emotion_info,
                        suggested_pictograms,
                        entities
                    )
            elif game_state["mode"] == "drill":
                target = (game_state.get("drill_target") or "").lower()
                if target and target in sentence_lower:
                    # correct, move to next round or finish after 3 rounds
                    if game_state.get("drill_round", 0) >= 2:
                        self.clear_user_game_state(username)
                        return self._package_response(self._single_entry_response("¡Genial! Practicamos tres pictos. ¿Quieres otro juego?"), intent_info, emotion_info, game_state.get("drill_items", []), entities)
                    next_prompt = self._drill_next_round(username, game_state.get("drill_items", []))
                    return self._package_response(next_prompt, intent_info, emotion_info, game_state.get("drill_items", []), entities)
                else:
                    # Re-show options as pictograms for clarity
                    options = []
                    for pic in game_state.get("drill_items", []):
                        kw = (pic.get('keywords') or [{}])[0].get('keyword', '')
                        options.append({'word': kw or '', 'pictogram': pic.get('path')})
                    prompt = [{'word': f"Elige o di: {game_state.get('drill_target')}.", 'pictogram': None}] + options
                    return self._package_response(prompt, intent_info, emotion_info, game_state.get("drill_items", []), entities)
            elif game_state["mode"] == "guided_session":
                if sentence_lower == game_state["correct_answer"].lower():
                    game_state["guided_session_step"] += 1
                    if game_state["guided_session_step"] < len(game_state["guided_session_words"]):
                        next_word = game_state["guided_session_words"][game_state["guided_session_step"]]
                        pictogram = nlp_utils.find_pictogram(next_word, nlp_utils.pictograms)
                        game_state["correct_answer"] = next_word
                        game_state["pictogram_path"] = pictogram['path'] if pictogram else None
                        prompt = (
                            "Eres un tutor AAC. Genera un refuerzo breve en español para un niño que acertó una palabra. "
                            f"Palabra: {next_word}. Sé cálido y usa menos de 15 palabras."
                        )
                        try:
                            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=256, truncation=True)
                            outputs = self.model.generate(inputs, max_length=60, num_beams=4, early_stopping=True)
                            success_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                        except Exception:
                            success_text = "¡Muy bien!"
                        return self._package_response(self._single_entry_response(success_text, game_state["pictogram_path"]), intent_info, emotion_info, suggested_pictograms, entities)
                    else:
                        self.clear_user_game_state(username)
                        prompt = (
                            "Eres un tutor AAC. Felicita en español a un niño por terminar una sesión guiada. "
                            "Usa menos de 18 palabras y tono alegre."
                        )
                        try:
                            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=256, truncation=True)
                            outputs = self.model.generate(inputs, max_length=60, num_beams=4, early_stopping=True)
                            farewell = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                        except Exception:
                            farewell = "¡Felicidades! Has completado la sesión."
                        return self._package_response(self._single_entry_response(farewell), intent_info, emotion_info, suggested_pictograms, entities)
                else:
                    game_state["failures"] += 1
                    clue = game_state["correct_answer"][:1 + game_state["failures"]]
                    prompt = (
                        "Eres un tutor AAC. Da una pista breve sin revelar la palabra completa. "
                        f"Letra inicial: {clue.upper()}. Máximo 12 palabras."
                    )
                    try:
                        inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=128, truncation=True)
                        outputs = self.model.generate(inputs, max_length=40, num_beams=4, early_stopping=True)
                        hint_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                    except Exception:
                        hint_text = f"La palabra comienza con {clue.upper()}."
                    return self._package_response(self._single_entry_response(hint_text, game_state["pictogram_path"]), intent_info, emotion_info, suggested_pictograms, entities)
        else:
            game_match = re.match(r"jugar a (.+)", sentence_lower)
            if game_match:
                category = game_match.group(1).strip()
                game_response = self.start_game(username, category)
                return self._package_response(self._single_entry_response(game_response['text'], game_response['pictogram']), intent_info, emotion_info, suggested_pictograms, entities)
            elif any(word in sentence_lower.split() for word in ["juego", "jugar", "juguemos"]):
                category = self._infer_category(sentence_lower)
                game_response = self.start_game(username, category)
                return self._package_response(self._single_entry_response(game_response['text'], game_response['pictogram']), intent_info, emotion_info, suggested_pictograms, entities)
            scripted = self._maybe_scripted_response(username, sentence_lower, role)
            if scripted:
                return self._package_response(scripted, intent_info, emotion_info, suggested_pictograms, entities)

            # Handle numeric-only inputs early with a clarifying prompt.
            digit_response = self._maybe_digit_response(sentence, intent_info, emotion_info, suggested_pictograms, entities)
            if digit_response:
                return digit_response

            # Start a pictogram drill if user asks to practice pictos.
            if any(trigger in sentence_lower for trigger in ["practicar pictos", "practicar pictogramas", "drill", "practica pictos"]):
                category = self._infer_category(sentence_lower)
                drill_intro = self._start_drill(username, category=category)
                # Surface drill pictos as suggestions so FE can render larger options.
                return self._package_response(drill_intro, intent_info, emotion_info, game_state.get("drill_items", []), entities)

            if intent_label == 'juego_pista':
                guess = self._semantic_card_match(sentence_lower)
                if guess:
                    pictogram = nlp_utils.find_pictogram(guess, nlp_utils.pictograms)
                    text = f"Creo que piensas en {guess}. Busca ese pictograma y dime si coincide."
                    return self._package_response(self._single_entry_response(text, pictogram['path'] if pictogram else None), intent_info, emotion_info, suggested_pictograms, entities)

            if intent_label == 'concepto_relacionado':
                related = self._related_vocab_response(sentence)
                if related:
                    return self._package_response(related, intent_info, emotion_info, suggested_pictograms, entities)

            if intent_label == 'consentimiento':
                return self._package_response(self._consent_response(username, sentence, sentence_lower), intent_info, emotion_info, suggested_pictograms, entities)

            if intent_label == 'emocional_checkin':
                return self._package_response(self._emotion_support_response(emotion_label), intent_info, emotion_info, suggested_pictograms, entities)

            if intent_label == 'factual_pregunta':
                return self._package_response(self._factual_response(sentence), intent_info, emotion_info, suggested_pictograms, entities)

            # If the question is a simple noun or "qué/cómo es" pattern, try a pictogram-based description first (only for very short inputs without digits).
            if not self._has_digits(sentence) and (re.search(r"\b(que es|qué es|como es|cómo es)\b", sentence_lower) or len(sentence_lower.split()) <= 2):
                described = self._describe_with_pictogram(sentence)
                if described:
                    return self._package_response(described, intent_info, emotion_info, suggested_pictograms, entities)

            # Quick option sampler when user asks for pictos/options.
            if "muestrame opciones de pictos" in sentence_lower or "muestrame pictos" in sentence_lower:
                sampled = self._sample_generic_pictos(4)
                prompt = [{'word': "Elige un picto para practicar:", 'pictogram': None}] + sampled
                return self._package_response(prompt, intent_info, emotion_info, sampled, entities)

            input_text = self._compose_transformer_input(username, sentence, role)
            try:
                inputs = self.tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
                outputs = self.model.generate(inputs, max_length=150, num_beams=4, early_stopping=True)
                response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception:
                fallback_text = DEFAULT_FALLBACK
                return self._package_response(self._wrap_text_with_pictograms(fallback_text), intent_info, emotion_info, suggested_pictograms, entities)

            if self._is_parroting(sentence, response_text) or len(response_text.split()) < 4:
                # Force a factual-style answer to avoid parroting.
                factual = self._factual_response(sentence)
                return self._package_response(factual, ('factual_pregunta', max(intent_score, 0.65)), emotion_info, suggested_pictograms, entities)

            if len(response_text.split()) < 3:
                described = self._describe_with_pictogram(sentence)
                if described:
                    return self._package_response(described, intent_info, emotion_info, suggested_pictograms, entities)
                choice = self._choice_prompt(suggested_pictograms)
                if choice:
                    return self._package_response(choice, intent_info, emotion_info, suggested_pictograms, entities)
                fallback_text = DEFAULT_FALLBACK
                return self._package_response(self._wrap_text_with_pictograms(fallback_text), intent_info, emotion_info, suggested_pictograms, entities)

            return self._package_response(self._wrap_text_with_pictograms(response_text), intent_info, emotion_info, suggested_pictograms, entities)

# Instantiate the chatbot
chatbot = Chatbot()


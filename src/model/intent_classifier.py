import os
import random
from pathlib import Path
from typing import Dict, Tuple

import spacy
from spacy.training import Example

MODEL_DIR = Path('data/models/intent_textcat')
LABELS = [
    'rutina_escolar',
    'terapia_habla',
    'juego_cooperativo',
    'autonomia_diaria',
    'factual_pregunta',
    'emocional_checkin',
    'juego_pista',
    'concepto_relacionado',
    'consentimiento',
    'otra_consulta'
]

TRAINING_DATA = [
    ('que hago antes de salir de casa', 'rutina_escolar'),
    ('necesito mis materiales para clase', 'rutina_escolar'),
    ('como me siento antes de la clase', 'rutina_escolar'),
    ('hora del recreo que hago', 'rutina_escolar'),
    ('recuérdame revisar la mochila', 'rutina_escolar'),
    ('ayudame a pronunciar la r', 'terapia_habla'),
    ('practicar sonido dificil', 'terapia_habla'),
    ('como repito mejor la palabra rana', 'terapia_habla'),
    ('dame ejercicios para terapia de lenguaje', 'terapia_habla'),
    ('quiero practicar mi voz', 'terapia_habla'),
    ('juguemos memoria con animales', 'juego_cooperativo'),
    ('dame una pista para el juego', 'juego_cooperativo'),
    ('que haria si mi amigo pierde', 'juego_cooperativo'),
    ('turno del juego ahora que', 'juego_cooperativo'),
    ('preguntas de juego cooperativo', 'juego_cooperativo'),
    ('como me lavo los dientes', 'autonomia_diaria'),
    ('pasos para vestirme solo', 'autonomia_diaria'),
    ('que hago antes de comer', 'autonomia_diaria'),
    ('ayudame con mi rutina de baño', 'autonomia_diaria'),
    ('quiero ser independiente para dormir', 'autonomia_diaria'),
    ('de que color es el cielo', 'factual_pregunta'),
    ('para que sirve un cepillo de dientes', 'factual_pregunta'),
    ('por que el sol brilla', 'factual_pregunta'),
    ('dime quien descubrio america', 'factual_pregunta'),
    ('cuantos dias tiene una semana', 'factual_pregunta'),
    ('estoy triste hoy', 'emocional_checkin'),
    ('tengo miedo de la clase', 'emocional_checkin'),
    ('me siento enojado', 'emocional_checkin'),
    ('estoy nervioso por la terapia', 'emocional_checkin'),
    ('me siento orgulloso por mi tarea', 'emocional_checkin'),
    ('dame una pista para esta carta', 'juego_pista'),
    ('es un animal grande con melena que puede ser', 'juego_pista'),
    ('que carta sigue en la memoria', 'juego_pista'),
    ('ayudame con la adivinanza', 'juego_pista'),
    ('necesito pista para el juego de cartas', 'juego_pista'),
    ('que palabras van con caballo', 'concepto_relacionado'),
    ('que combina con bicicleta', 'concepto_relacionado'),
    ('dime palabras relacionadas con casa', 'concepto_relacionado'),
    ('como se relaciona perro con hueso', 'concepto_relacionado'),
    ('dame vocabulario de animales de granja', 'concepto_relacionado'),
    ('puedo descansar un momento', 'consentimiento'),
    ('me dejas llamar a mama', 'consentimiento'),
    ('puedo tomar agua por favor', 'consentimiento'),
    ('esta bien si paro la actividad', 'consentimiento'),
    ('podemos compartir esta informacion', 'consentimiento'),
    ('no se que decir', 'otra_consulta'),
    ('cuentame algo divertido', 'otra_consulta'),
    ('hola solo quiero hablar', 'otra_consulta'),
    ('no entiendo la actividad', 'otra_consulta'),
    ('puedes repetir lo anterior', 'otra_consulta')
]

_intent_nlp = None


def _train_model() -> spacy.language.Language:
    nlp = spacy.blank('es')
    textcat = nlp.add_pipe('textcat', config={'exclusive_classes': True, 'architecture': 'simple_cnn'})
    for label in LABELS:
        textcat.add_label(label)

    training_examples = []
    for text, label in TRAINING_DATA:
        cats = {lab: 0.0 for lab in LABELS}
        cats[label] = 1.0
        training_examples.append(Example.from_dict(nlp.make_doc(text), {'cats': cats}))

    optimizer = nlp.initialize(lambda: training_examples)
    for epoch in range(25):
        random.shuffle(training_examples)
        losses = {}
        batches = spacy.util.minibatch(training_examples, size=4)
        for batch in batches:
            nlp.update(batch, sgd=optimizer, losses=losses)
        # optional: could print losses, but avoid stdout noise

    MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(MODEL_DIR)
    return nlp


def _load_or_train() -> spacy.language.Language:
    if MODEL_DIR.exists():
        try:
            return spacy.load(MODEL_DIR)
        except Exception:
            pass
    return _train_model()


def _ensure_model():
    global _intent_nlp
    if _intent_nlp is None:
        _intent_nlp = _load_or_train()
    return _intent_nlp


def predict_intent(text: str) -> Tuple[str, float]:
    """Returns best intent label and score between 0-1."""
    if not text:
        return 'otra_consulta', 0.0
    nlp = _ensure_model()
    doc = nlp(text.lower())
    if not doc.cats:
        return 'otra_consulta', 0.0
    label = max(doc.cats, key=doc.cats.get)
    return label, float(doc.cats[label])


def intent_distribution(text: str) -> Dict[str, float]:
    nlp = _ensure_model()
    doc = nlp(text.lower())
    return dict(doc.cats)

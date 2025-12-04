import random
from pathlib import Path
from typing import Dict, Tuple

import spacy
from spacy.training import Example

MODEL_DIR = Path('data/models/emotion_textcat')
EMOTIONS = ['triste', 'ansioso', 'enojado', 'orgulloso', 'calmo', 'neutral']

TRAINING_DATA = [
    ('estoy muy triste porque extraño a mi mama', 'triste'),
    ('me siento solo y me dieron ganas de llorar', 'triste'),
    ('tengo miedo de entrar a clase', 'ansioso'),
    ('me preocupa equivocarme frente a todos', 'ansioso'),
    ('estoy enojado y quiero gritar', 'enojado'),
    ('me molesta que no salga bien el juego', 'enojado'),
    ('estoy orgulloso de mi dibujo', 'orgulloso'),
    ('me siento muy contento con mi progreso', 'orgulloso'),
    ('estoy tranquilo leyendo un cuento', 'calmo'),
    ('respire y ahora me siento en calma', 'calmo'),
    ('solo quiero hablar un momento', 'neutral'),
    ('no se como me siento hoy', 'neutral'),
]

_emotion_nlp = None


def _train_model() -> spacy.language.Language:
    nlp = spacy.blank('es')
    textcat = nlp.add_pipe('textcat', config={'exclusive_classes': True, 'architecture': 'simple_cnn'})
    for label in EMOTIONS:
        textcat.add_label(label)

    training_examples = []
    for text, label in TRAINING_DATA:
        cats = {lab: 0.0 for lab in EMOTIONS}
        cats[label] = 1.0
        training_examples.append(Example.from_dict(nlp.make_doc(text), {'cats': cats}))

    optimizer = nlp.initialize(lambda: training_examples)
    for epoch in range(20):
        random.shuffle(training_examples)
        losses = {}
        batches = spacy.util.minibatch(training_examples, size=3)
        for batch in batches:
            nlp.update(batch, sgd=optimizer, losses=losses)
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
    global _emotion_nlp
    if _emotion_nlp is None:
        _emotion_nlp = _load_or_train()
    return _emotion_nlp


def predict_emotion(text: str) -> Tuple[str, float]:
    if not text:
        return 'neutral', 0.0
    nlp = _ensure_model()
    doc = nlp(text.lower())
    if not doc.cats:
        return 'neutral', 0.0
    label = max(doc.cats, key=doc.cats.get)
    return label, float(doc.cats[label])


def emotion_distribution(text: str) -> Dict[str, float]:
    nlp = _ensure_model()
    doc = nlp(text.lower())
    return dict(doc.cats)

import numpy as np
from functools import lru_cache
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def _get_model():
    return SentenceTransformer(MODEL_NAME)


def build_dense_index(pictograms):
    """Build an in-memory dense index for pictograms using their first keyword."""
    model = _get_model()
    index = []
    texts = []
    for pic in pictograms:
        keywords = pic.get("keywords") or []
        if not keywords:
            continue
        keyword = keywords[0].get("keyword") if isinstance(keywords[0], dict) else keywords[0]
        if not keyword:
            continue
        texts.append(keyword)
        index.append({"path": pic.get("path"), "keyword": keyword})
    if not texts:
        return [], np.zeros((0, 384), dtype=np.float32)
    embeddings = model.encode(texts, normalize_embeddings=True)
    return index, embeddings


def top_k(text: str, index, embeddings, k: int = 5):
    if not text or embeddings.shape[0] == 0:
        return []
    model = _get_model()
    query = model.encode(text, normalize_embeddings=True)
    scores = embeddings @ query
    top_idx = np.argsort(-scores)[:k]
    results = []
    for idx in top_idx:
        entry = index[int(idx)]
        results.append({
            "path": entry.get("path"),
            "keyword": entry.get("keyword"),
            "score": float(scores[idx])
        })
    return results

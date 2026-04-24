from __future__ import annotations

from ml_classifier.model import load_model
from ml_classifier.preprocessor import preprocess_bytes

_model = None
DEBRIS_THRESHOLD = 0.5


def _get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model


def classify_image(image_bytes: bytes) -> dict:
    """
    Returns {"label": "clean" | "debris", "confidence": float}.
    """
    img = preprocess_bytes(image_bytes)
    model = _get_model()
    prob = float(model.predict(img, verbose=0)[0][0])

    if prob >= DEBRIS_THRESHOLD:
        return {"label": "debris", "confidence": round(prob, 4)}
    return {"label": "clean", "confidence": round(1.0 - prob, 4)}

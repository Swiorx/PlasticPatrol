import cv2
import numpy as np

TARGET_SIZE = (224, 224)


def preprocess_bytes(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes and return a (1, 224, 224, 3) float32 array."""
    buf = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image — unsupported format or corrupt data")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, TARGET_SIZE, interpolation=cv2.INTER_AREA)
    img = img.astype(np.float32) / 255.0
    return np.expand_dims(img, axis=0)


def preprocess_path(image_path: str) -> np.ndarray:
    """Load an image from disk and preprocess it."""
    with open(image_path, "rb") as f:
        return preprocess_bytes(f.read())

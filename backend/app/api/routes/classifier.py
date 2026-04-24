from fastapi import APIRouter, File, HTTPException, UploadFile
import sys
from pathlib import Path

# Adaugam radacina proiectului in calea sistemului pentru a gasi ml_classifier
ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

router = APIRouter(prefix="/classify", tags=["classifier"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("")
async def classify_image(file: UploadFile = File(...)):
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported image type. Use JPEG, PNG, or WebP.")

    image_bytes = await file.read()
    if len(image_bytes) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image too large. Maximum size is 10 MB.")

    try:
        from ml_classifier.predict import classify_image as _classify
        result = _classify(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare interna ML: {str(e)}")

    return result

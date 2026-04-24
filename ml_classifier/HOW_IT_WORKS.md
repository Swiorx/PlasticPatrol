# ML Classifier — How It Works & How to Test

## Overview

The classifier is a binary image classifier that detects whether a water image contains
plastic debris or is clean. It is exposed as a FastAPI endpoint and uses a Keras/TensorFlow
model trained on ocean imagery.

---

## Architecture

```
POST /api/classify  (multipart image upload)
         │
         ▼
backend/app/api/routes/classifier.py
  - validates content type (JPEG, PNG, WebP)
  - validates file size (max 10 MB)
         │
         ▼
ml_classifier/predict.py  →  classify_image(bytes)
  - calls preprocessor to resize image to 224×224
  - runs inference on loaded Keras model
  - returns {"label": "clean"|"debris", "confidence": float}
         │
         ▼
ml_classifier/model.py  →  load_model()
  - loads weights/classifier.keras (EfficientNet-based binary classifier)
  - model internally applies ImageNet preprocessing (rescaling + normalization)
```

### Key files

| File | Purpose |
|------|---------|
| `ml_classifier/model.py` | `build_model()`, `load_model()`, `save_model()` |
| `ml_classifier/preprocessor.py` | Resize + convert image bytes to (1, 224, 224, 3) float32 array |
| `ml_classifier/predict.py` | Orchestrates preprocessing → inference → result dict |
| `ml_classifier/train.py` | Offline training script (see Training section) |
| `ml_classifier/weights/classifier.keras` | Trained model weights |
| `backend/app/api/routes/classifier.py` | FastAPI route, input validation |

### Model architecture

The saved model (`classifier.keras`) is an **EfficientNet-based transfer learning model** with:

- Built-in preprocessing: `Rescaling(1/255)` → ImageNet `Normalization` → inverse rescaling
- `GlobalAveragePooling2D`
- `Dropout(0.3)` → `Dense(128, relu)` → `Dropout(0.2)` → `Dense(1, sigmoid)`

Input: `(224, 224, 3)` float32, pixel values in **[0, 1]** range (preprocessor handles this).
Output: single sigmoid probability — values ≥ 0.5 → `"debris"`, < 0.5 → `"clean"`.

---

## Training data

```
data/
  clean/    200 images of clean ocean water
  debris/   900 images of ocean water with plastic/debris
```

The training script automatically **balances** classes by undersampling the majority class,
resulting in 200 images per class (400 total).

---

## Training the model

```bash
cd /home/kalimatei/plasticpatrol/PlasticPatrol

# Install dependencies
pip install tensorflow keras opencv-python-headless

# Train (default 20 epochs with early stopping)
python -m ml_classifier.train --data_dir ./data --epochs 20

# Weights are saved to ml_classifier/weights/classifier.keras
```

> **Note:** With only 200 images per class, training may underfit. Collect more clean-water
> images (target: 500+ per class) for reliable accuracy.

**Known issue with current weights:** The model in `weights/classifier.keras` was trained
with a double-normalization bug (training script applied `Rescaling(1/255)` externally while
the EfficientNet base also applies it internally). As a result the current weights predict
everything as "clean" with ~0.55 confidence. **Retrain the model** using the fixed training
script to get accurate predictions.

---

## Testing the classifier

### 1. Quick Python test (no server needed)

```python
from ml_classifier.predict import classify_image

# Test with a debris image
with open("data/debris/oceancv_00000.jpg", "rb") as f:
    result = classify_image(f.read())
print(result)
# Expected: {"label": "debris", "confidence": 0.XXXX}

# Test with a clean image
with open("data/clean/clean_00000.jpg", "rb") as f:
    result = classify_image(f.read())
print(result)
# Expected: {"label": "clean", "confidence": 0.XXXX}
```

### 2. Batch accuracy test

```python
import os
from ml_classifier.predict import classify_image

def run_batch(folder, expected_label):
    files = sorted(os.listdir(folder))[:10]
    correct = 0
    for fname in files:
        with open(os.path.join(folder, fname), "rb") as f:
            result = classify_image(f.read())
        ok = "CORRECT" if result["label"] == expected_label else "WRONG"
        print(f"  {fname}: {result}  [{ok}]")
        correct += result["label"] == expected_label
    print(f"  Accuracy: {correct}/{len(files)}\n")

print("=== DEBRIS ===")
run_batch("data/debris", "debris")

print("=== CLEAN ===")
run_batch("data/clean", "clean")
```

### 3. Via the FastAPI endpoint (server must be running)

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# In another terminal — submit a debris image
curl -X POST http://localhost:8000/api/classify \
  -F "file=@../data/debris/oceancv_00000.jpg"

# Expected response
# {"label":"debris","confidence":0.87}
```

### 4. Error cases to verify

```bash
# Too large (> 10 MB) — expect 413
curl -X POST http://localhost:8000/api/classify \
  -F "file=@large_file.bin"

# Wrong type (PDF) — expect 415
curl -X POST http://localhost:8000/api/classify \
  -F "file=@document.pdf;type=application/pdf"
```

---

## Current test results (as of April 2026)

```
DEBRIS IMAGES (expected: debris)
  oceancv_00000.jpg: {'label': 'clean', 'confidence': 0.5525}  [WRONG]
  oceancv_00001.jpg: {'label': 'clean', 'confidence': 0.5525}  [WRONG]
  ...

CLEAN IMAGES (expected: clean)
  clean_00000.jpg: {'label': 'clean', 'confidence': 0.5528}  [CORRECT]
  ...
```

All predictions land near 0.55 regardless of image content — the model weights need to be
regenerated by retraining. The pipeline itself (API → preprocessor → model → response) is
fully functional.

---

## Retraining checklist

1. Collect more clean-water images (currently only 200; aim for 500+)
2. Run `python -m ml_classifier.train --data_dir ./data --epochs 30`
3. Monitor `val_auc` — early stopping will save the best checkpoint
4. Run the batch accuracy test above to verify ≥ 80% accuracy on both classes
5. Restart the FastAPI server so the new weights are loaded

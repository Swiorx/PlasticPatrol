from pathlib import Path

import keras

MODEL_DIR = Path(__file__).parent / "weights"
MODEL_PATH = MODEL_DIR / "classifier.keras"

INPUT_SHAPE = (224, 224, 3)
NUM_CLASSES = 1  # binary: clean vs debris


def build_model() -> keras.Model:
    base = keras.applications.MobileNetV2(
        input_shape=INPUT_SHAPE, include_top=False, weights="imagenet"
    )
    base.trainable = False

    x = base.output
    x = keras.layers.GlobalAveragePooling2D()(x)
    x = keras.layers.Dense(128, activation="relu")(x)
    x = keras.layers.Dropout(0.3)(x)
    output = keras.layers.Dense(NUM_CLASSES, activation="sigmoid")(x)

    model = keras.Model(inputs=base.input, outputs=output)
    model.compile(
        optimizer=keras.optimizers.Adam(1e-4),
        loss="binary_crossentropy",
        metrics=["accuracy", keras.metrics.AUC(name="auc")],
    )
    return model


def save_model(model: keras.Model) -> None:
    MODEL_DIR.mkdir(exist_ok=True)
    model.save(str(MODEL_PATH))


def load_model() -> keras.Model:
    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Model weights not found at {MODEL_PATH}. "
            "Train first: python -m ml_classifier.train --data_dir ./data"
        )
    return keras.models.load_model(str(MODEL_PATH))

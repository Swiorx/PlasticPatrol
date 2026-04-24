"""
Offline training script.

Expected dataset layout:
    data/
        clean/      <-- images of clean ocean water
        debris/     <-- images of water with plastic/debris

Usage:
    python -m ml_classifier.train --data_dir ./data --epochs 20
"""

import argparse
import pathlib
import random
import shutil
import tempfile

import tensorflow as tf

from ml_classifier.model import build_model, save_model

IMG_SIZE = (224, 224)
BATCH_SIZE = 16


def _balance_to_tmp(data_dir: str) -> tuple[str, bool]:
    """
    Copy images to a temp directory, undersampling the majority class so both
    classes have the same count. Returns (tmp_dir_path, created_tmp).
    """
    root = pathlib.Path(data_dir)
    clean = sorted((root / "clean").glob("*.*"))
    debris = sorted((root / "debris").glob("*.*"))

    n_min = min(len(clean), len(debris))
    if n_min == 0:
        raise ValueError(f"One of the classes has no images in {data_dir}")

    if len(clean) == len(debris):
        return data_dir, False  # already balanced, no copy needed

    print(f"  Balancing: {len(clean)} clean / {len(debris)} debris → using {n_min} each")
    random.seed(42)
    clean_sample = random.sample(clean, n_min)
    debris_sample = random.sample(debris, n_min)

    tmp = tempfile.mkdtemp(prefix="plasticpatrol_train_")
    (pathlib.Path(tmp) / "clean").mkdir()
    (pathlib.Path(tmp) / "debris").mkdir()
    for f in clean_sample:
        shutil.copy2(f, pathlib.Path(tmp) / "clean" / f.name)
    for f in debris_sample:
        shutil.copy2(f, pathlib.Path(tmp) / "debris" / f.name)
    return tmp, True


def build_datasets(data_dir: str, validation_split: float = 0.2):
    augment = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal_and_vertical"),
        tf.keras.layers.RandomRotation(0.1),
        tf.keras.layers.RandomZoom(0.1),
        tf.keras.layers.RandomBrightness(0.1),
        tf.keras.layers.RandomContrast(0.1),
    ])
    normalize = tf.keras.layers.Rescaling(1.0 / 255)

    common = dict(
        directory=data_dir,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="binary",
        seed=42,
    )
    train_ds = tf.keras.utils.image_dataset_from_directory(
        **common, validation_split=validation_split, subset="training"
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        **common, validation_split=validation_split, subset="validation"
    )

    train_ds = (
        train_ds
        .map(lambda x, y: (normalize(x), y), num_parallel_calls=tf.data.AUTOTUNE)
        .map(lambda x, y: (augment(x, training=True), y), num_parallel_calls=tf.data.AUTOTUNE)
        .prefetch(tf.data.AUTOTUNE)
    )
    val_ds = (
        val_ds
        .map(lambda x, y: (normalize(x), y), num_parallel_calls=tf.data.AUTOTUNE)
        .prefetch(tf.data.AUTOTUNE)
    )
    return train_ds, val_ds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()

    balanced_dir, is_tmp = _balance_to_tmp(args.data_dir)
    try:
        train_ds, val_ds = build_datasets(balanced_dir)

        model = build_model()
        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor="val_auc", patience=5,
                                             restore_best_weights=True, mode="max"),
            tf.keras.callbacks.ReduceLROnPlateau(monitor="val_auc", patience=3,
                                                 factor=0.5, mode="max"),
        ]

        model.fit(train_ds, validation_data=val_ds, epochs=args.epochs, callbacks=callbacks)
        save_model(model)
        print("Model saved to ml_classifier/weights/classifier.keras")
    finally:
        if is_tmp:
            shutil.rmtree(balanced_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

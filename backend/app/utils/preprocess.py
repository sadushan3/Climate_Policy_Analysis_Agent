from __future__ import annotations
import pickle
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# ---------- Paths (project-relative) ----------
ROOT = Path(__file__).resolve().parents[1]        # project root = parent of this file's folder
ART_DIR = ROOT / "artifacts"
DATA_DIR = ROOT / "data"
DATA_PATH = DATA_DIR / "weather_samples.csv"
ART_PATH = ART_DIR / "weather_data.pkl"

FEATURES = ["location", "month", "temperature_c", "humidity_pct", "wind_kmh"]
TARGET = "condition"


def fit_and_serialize(data_path: Path = DATA_PATH, out_path: Path = ART_PATH) -> Path:
    """Fit preprocessing pipeline on CSV and serialize artifacts (.pkl)."""
    ART_DIR.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(
            f"Training data not found at {data_path}. "
            f"Expected columns: {FEATURES + [TARGET]}"
        )

    df = pd.read_csv(data_path)
    missing = set(FEATURES + [TARGET]) - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    X = df[FEATURES]
    # y kept for future model training if needed
    # y = df[TARGET]

    cat_features = ["location", "month"]
    num_features = ["temperature_c", "humidity_pct", "wind_kmh"]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
            ("num", StandardScaler(), num_features),
        ]
    )

    pipe = Pipeline([("pre", pre)]).fit(X)

    with out_path.open("wb") as f:
        pickle.dump({"pipeline": pipe, "raw_df": df}, f)

    return out_path


def load_artifacts(path: Path = ART_PATH):
    """
    Load artifacts; if pickle missing, rebuild from CSV.
    Raises clear errors if CSV also missing or invalid.
    """
    try:
        if not path.exists():
            fit_and_serialize(DATA_PATH, path)
        with path.open("rb") as f:
            return pickle.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Artifacts and/or data are missing. "
            f"Searched for pickle at {path} and CSV at {DATA_PATH}."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to load artifacts from {path}: {e}") from e


def export_readable(
    pickle_path: Path = ART_PATH,
    out_dir: Path = ART_DIR,
    preview_rows: int = 10,
) -> dict:
    """
    Create human-readable files alongside the pickle:
      - artifacts/raw_preview.csv  (first N rows)
      - artifacts/metadata.json    (small summary)
    Returns paths in a dict.
    """
    import json

    obj = load_artifacts(pickle_path)
    if not isinstance(obj, dict) or "pipeline" not in obj or "raw_df" not in obj:
        raise ValueError("Unexpected artifact format. Expected dict with 'pipeline' and 'raw_df'.")

    out_dir.mkdir(parents=True, exist_ok=True)

    # CSV preview of the raw data
    csv_path = out_dir / "raw_preview.csv"
    obj["raw_df"].head(preview_rows).to_csv(csv_path, index=False)

    # Minimal metadata (readable in any text editor)
    meta = {
        "pipeline_steps": [name for name, _ in obj["pipeline"].steps],
        "n_rows": int(obj["raw_df"].shape[0]),
        "n_cols": int(obj["raw_df"].shape[1]),
        "feature_columns": FEATURES,
        "target_column": TARGET,
    }
    meta_path = out_dir / "metadata.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {"csv": str(csv_path), "metadata": str(meta_path)}


# Optional: CLI helpers for quick use
if __name__ == "__main__":
    # 1) Build/refresh pickle
    out = fit_and_serialize()
    print(f"Artifacts written: {out}")

    # 2) Export human-readable preview
    paths = export_readable()
    print(f"Readable exports: {paths}")

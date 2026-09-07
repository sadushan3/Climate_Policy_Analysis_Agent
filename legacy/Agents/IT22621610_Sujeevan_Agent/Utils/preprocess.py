import os
import pickle
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

ART_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_PATH = os.path.join(DATA_DIR, "weather_samples.csv")
ART_PATH = os.path.join(ART_DIR, "weather_data.pkl")

FEATURES = ["location","month","temperature_c","humidity_pct","wind_kmh"]
TARGET = "condition"

def fit_and_serialize(data_path: str = DATA_PATH, out_path: str = ART_PATH):
    df = pd.read_csv(data_path)
    X = df[FEATURES]
    y = df[TARGET]

    cat_features = ["location","month"]
    num_features = ["temperature_c","humidity_pct","wind_kmh"]

    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
        ("num", StandardScaler(), num_features),
    ])

    pipe = Pipeline([("pre", pre)]).fit(X)

    # Save artifacts
    with open(out_path, "wb") as f:
        pickle.dump({
            "pipeline": pipe,
            "raw_df": df
        }, f)

    return out_path

def load_artifacts(path: str = ART_PATH):
    if not os.path.exists(path):
        fit_and_serialize()
    with open(path, "rb") as f:
        return pickle.load(f)

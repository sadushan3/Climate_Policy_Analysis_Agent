import os
import pickle
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List

# Constants
FEATURES = ["location", "month", "temperature_c", "humidity_pct", "wind_kmh"]
TARGET = "condition"

class WeatherDataProcessor:
    def __init__(self, data_dir: str = "data", artifacts_dir: str = "artifacts"):
        self.data_dir = data_dir
        self.artifacts_dir = artifacts_dir
        self.data_path = os.path.join(data_dir, "weather_samples.csv")
        self.art_path = os.path.join(artifacts_dir, "weather_data.pkl")

    def fit_and_serialize(self, data_path: str = None, out_path: str = None):
        data_path = data_path or self.data_path
        out_path = out_path or self.art_path

        df = pd.read_csv(data_path)
        X = df[FEATURES]
        y = df[TARGET]

        cat_features = ["location", "month"]
        num_features = ["temperature_c", "humidity_pct", "wind_kmh"]

        pre = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
            ("num", StandardScaler(), num_features),
        ])

        pipe = Pipeline([("pre", pre)]).fit(X)

        # Save artifacts
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            pickle.dump({
                "pipeline": pipe,
                "raw_df": df
            }, f)

        return out_path

    def load_artifacts(self, path: str = None):
        path = path or self.art_path
        if not os.path.exists(path):
            self.fit_and_serialize()
        with open(path, "rb") as f:
            return pickle.load(f)

    def recommend(self, query: Dict, top_n: int = 5) -> Dict:
        art = self.load_artifacts()
        pipe = art["pipeline"]
        df = art["raw_df"]

        # Transform historical features
        X_hist = pipe.transform(df[FEATURES])

        # Build a single-row dataframe for the query
        q_df = pd.DataFrame([{k: query[k] for k in FEATURES}])
        X_q = pipe.transform(q_df)

        # Compute cosine similarity
        sims = cosine_similarity(X_q, X_hist)[0]
        idx_sorted = np.argsort(sims)[::-1][:top_n]

        top_rows = df.iloc[idx_sorted].copy()
        top_sims = sims[idx_sorted]

        # Aggregate predicted condition (majority vote weighted by similarity)
        from collections import Counter
        weighted = {}
        for cond, s in zip(top_rows["condition"], top_sims):
            weighted[cond] = weighted.get(cond, 0.0) + float(s)
        predicted_condition, confidence = max(weighted.items(), key=lambda kv: kv[1])
        total = sum(weighted.values()) or 1.0
        conf_norm = confidence / total

        # Build response list
        top_similar = []
        for (_, row), sim in zip(top_rows.iterrows(), top_sims):
            top_similar.append({
                "location": row["location"],
                "month": int(row["month"]),
                "temperature_c": float(row["temperature_c"]),
                "humidity_pct": int(row["humidity_pct"]),
                "wind_kmh": float(row["wind_kmh"]),
                "condition": row["condition"],
                "similarity": float(sim),
            })

        return {
            "predicted_condition": predicted_condition,
            "confidence": float(conf_norm),
            "top_similar_days": top_similar,
            "message": "Content-based recommendation using cosine similarity on historical weather-like features."
        }
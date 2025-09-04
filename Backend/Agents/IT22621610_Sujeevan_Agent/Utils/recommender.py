import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .preprocess import load_artifacts, FEATURES

def recommend(query: dict, top_n: int = 5):
    art = load_artifacts()
    pipe = art["pipeline"]
    df = art["raw_df"]

    # Transform historical features
    X_hist = pipe.transform(df[FEATURES])

    # Build a single-row dataframe for the query
    import pandas as pd
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

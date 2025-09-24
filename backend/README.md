# Weather Prediction Recommendation (FastAPI)

## Structure

```
weather_recommendation/
├── main.py
├── routes/
│   └── recommendations.py
├── models/
│   └── schemas.py
├── utils/
│   ├── preprocess.py
│   └── recommender.py
├── data/
│   └── weather_samples.csv   # placeholder data – replace with your real dataset
└── artifacts/
    └── weather_data.pkl      # auto-created pipeline artifacts
```

## How it works

- **utils/preprocess.py**: fits a preprocessing pipeline (OneHot for categorical, scaling for numeric) on the CSV and serializes artifacts.
- **utils/recommender.py**: computes **cosine similarity** between an incoming query and historical rows to recommend the **likely weather condition** and show the **top similar days**.
- **routes/recommendations.py**: FastAPI endpoint `POST /api/recommendations` that accepts a `WeatherQuery` and returns a `RecommendationResponse`.
- **main.py**: wires everything and exposes `/docs` for Swagger UI.

## Quickstart

1. (Optional) Create & activate a venv.
2. Install deps:

```bash
pip install fastapi uvicorn scikit-learn pandas numpy
```

3. Run the API:

```bash
uvicorn main:app --reload
```

4. Open docs: http://127.0.0.1:8000/docs

### Example request (JSON)
```json
{
  "location": "Colombo",
  "month": 8,
  "temperature_c": 29.5,
  "humidity_pct": 78,
  "wind_kmh": 10.0
}
```

### Response (sample)
```json
{
  "predicted_condition": "Sunny",
  "confidence": 0.62,
  "top_similar_days": [ ... ],
  "message": "Content-based recommendation using cosine similarity on historical weather-like features."
}
```

## Swapping in your real dataset

Replace `data/weather_samples.csv` with your historical weather facts with **these minimum columns**:

- `location` (str)
- `month` (1..12)
- `temperature_c` (float)
- `humidity_pct` (0..100)
- `wind_kmh` (float)
- `condition` (target label: e.g., Sunny / Rain / Cloudy / ...)

Then call any endpoint (or import and run `fit_and_serialize()` from `utils.preprocess`) to regenerate artifacts.

## Notes

- This mirrors your original content-based approach (cosine similarity) and keeps a maintainable separation of **routes / models / utils**.
- You can add additional features (e.g., `pressure`, `cloud_cover`, `precip_mm`) by updating `FEATURES` in `utils/preprocess.py`.
- If you want a Streamlit UI like your gym prototype, we can add it under a `ui/` folder that calls the FastAPI.

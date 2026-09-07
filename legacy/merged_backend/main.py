import sys, os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.routes import router
import uvicorn
import logging
import spacy
from transformers import pipeline
from models.models import ComparatorModel
from utils.weather_utils import WeatherDataProcessor

# Logging setup
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler(sys.stdout)]
)

app = FastAPI(title="Climate Policy Analysis API", version="1.0.0")

@app.on_event("startup")
async def load_models():
    try:
        app.state.nlp = spacy.load("en_core_web_sm")
        app.state.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        app.state.comparator = ComparatorModel()
        app.state.weather_processor = WeatherDataProcessor()
        logging.info("✅ All models loaded successfully")
    except Exception as e:
        logging.error(f"❌ Model load error: {str(e)}")
        raise

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Routes
app.include_router(router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "ok", "models_loaded": True}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.recommendations import router as rec_router

app = FastAPI(title="Weather Prediction Recommendation API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rec_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "service": "weather-recommendation", "docs": "/docs", "ui": "/app"}

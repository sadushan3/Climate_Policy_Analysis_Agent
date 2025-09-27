from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.routes import router as preprocess_router
from dotenv import load_dotenv

# Load .env for this agent
load_dotenv()

app = FastAPI(title="Climate Policy Preprocessing API (IT22106056_Dhanaga_Agent)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes under a clear prefix to avoid collisions
app.include_router(preprocess_router, prefix="/api/preprocess", tags=["Preprocessing"])

@app.get("/")
def root():
    return {"message": "Preprocessing API is running", "routes_prefix": "/api/preprocess"}

# For local running: uvicorn Backend.Agents.IT22106056_Dhanaga_Agent.app:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Backend.Agents.IT22106056_Dhanaga_Agent.app:app", host="127.0.0.1", port=8000, reload=True)

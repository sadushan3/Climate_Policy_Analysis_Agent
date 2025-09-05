from fastapi import FastAPI
from Backend.Agents.IT22180520_Sadushan_Agent.Routes import Routes
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Climatic Policy AI - Policy Comparator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Must allow OPTIONS for preflight
    allow_headers=["*"],
)

app.include_router(Routes.router, prefix="/api", tags=["Policy Comparator"])

@app.get("/")
def root():
    return {"message": "Policy Comparator Agent API is running securely "}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Backend.Agents.Main:app", host="127.0.0.1", port=8000, reload=True)
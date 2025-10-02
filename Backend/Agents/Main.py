from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="Climate Policy Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Must allow OPTIONS for preflight
    allow_headers=["*"],
)

from Backend.Agents.IT22180520_Sadushan_Agent.Routes import Routes, policy_routes

# Include routers
app.include_router(Routes.router, prefix="/api", tags=["Policy Comparator"])
app.include_router(policy_routes.router, prefix="/api/policy", tags=["Document Analysis"])

@app.get("/")
def root():
    return {"message": "Policy Comparator Agent API is running securely "}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Backend.Agents.Main:app", host="127.0.0.1", port=8000, reload=True)
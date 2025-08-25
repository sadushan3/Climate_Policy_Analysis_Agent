from fastapi import FastAPI
from Backend.Agents.IT22180520_Sadushan_Agent.Routes import comparator_routes
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app=FastAPI(title="Climatic Policy AI - Policy Comparator")

origins=os.getenv("ALLOWED_ORIGINS","*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],

)

app.include_router(comparator_routes.router, prefix="/api", tags=["Policy Comparator"])

@app.get("/")
def root():
    return {"message": "Policy Comparator Agent API is running securely "}
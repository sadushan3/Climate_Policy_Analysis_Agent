from IT22106056_Dhanaga_Agent.routes import upload_router
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
from datetime import datetime
from pathlib import Path


app = FastAPI(
    title="Climate Policy Analysis API",
    description="API for uploading and preprocessing climate policy documents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router.router, prefix="/api/v1", tags=["Document Upload"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Climate Policy Analysis API",
        "status": "running",
        "documentation": "/docs"
    }

# Print all registered routes
print("\nRegistered routes:")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = route.methods if hasattr(route, 'methods') else []
        print(f"{', '.join(methods)} {route.path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

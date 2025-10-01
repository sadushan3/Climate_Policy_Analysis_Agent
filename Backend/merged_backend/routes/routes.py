from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, List
import logging
import os
from pydantic import BaseModel

from models.models import PolicyAnalysis, WeatherQuery, RecommendationResponse, ComparatorModel
from utils.analysis_utils import analyze_document, summarize_text, extract_entities
from utils.file_utils import extract_text_from_pdf
from utils.text_utils import sanitize_text, validate_policy_input
from utils.weather_utils import WeatherDataProcessor

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize routers
router = APIRouter()
weather_router = APIRouter(prefix="/recommendations", tags=["recommendations"])
policy_router = APIRouter(prefix="/policy", tags=["policy"])

# Initialize models
comparator_model = ComparatorModel()
weather_processor = WeatherDataProcessor()

# Weather Routes
@weather_router.post("/", response_model=RecommendationResponse)
def get_recommendations(q: WeatherQuery):
    try:
        result = weather_processor.recommend(q.dict(), top_n=5)
        return result
    except Exception as e:
        logging.error(f"Error in weather recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Policy Analysis Routes
@policy_router.post("/analyze", response_model=PolicyAnalysis)
async def analyze_document_api(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}
    try:
        text = extract_text_from_pdf(file.file)
        result = analyze_document(text)
        return result
    except Exception as e:
        logging.error(f"Error in document analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@policy_router.post("/summarize")
async def summarize_api(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}
    try:
        text = extract_text_from_pdf(file.file)
        summary = summarize_text(text)
        return {"summary": summary}
    except Exception as e:
        logging.error(f"Error in document summarization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@policy_router.post("/ner")
async def ner_api(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}
    try:
        text = extract_text_from_pdf(file.file)
        entities = extract_entities(text)
        return {"entities": entities}
    except Exception as e:
        logging.error(f"Error in named entity recognition: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@policy_router.post("/full-analysis")
async def full_analysis_api(file: UploadFile = File(...)):
    """
    Upload a PDF and get:
    1. Structured Policy Analysis
    2. Policy Summary
    3. Named Entities
    """
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}

    try:
        text = extract_text_from_pdf(file.file)
        analysis = analyze_document(text)
        summary = summarize_text(text)
        entities = extract_entities(text)

        return {
            "document_name": file.filename,
            "word_count": len(text.split()),
            "analysis": analysis.dict(),
            "summary": summary,
            "entities": entities
        }
    except Exception as e:
        logging.error(f"Error in full analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class PolicyCompareRequest(BaseModel):
    policy1: str
    policy2: str

@policy_router.post("/compare")
def compare_policy(request: PolicyCompareRequest):
    if not validate_policy_input(request.policy1) or not validate_policy_input(request.policy2):
        logging.warning("Invalid policy input detected")
        raise HTTPException(status_code=400, detail="Invalid or too short policy text")

    try:
        policy1 = sanitize_text(request.policy1)
        policy2 = sanitize_text(request.policy2)

        similarity_score = comparator_model.compute_similarity(policy1, policy2)
        comparison = comparator_model.extract_overlap_unique(policy1, policy2)

        logging.info(
            f"Policy comparison done | Similarity: {similarity_score:.2f} | "
            f"Overlap: {len(comparison['overlap'])} | "
            f"Unique A: {len(comparison['unique_policy1'])} | "
            f"Unique B: {len(comparison['unique_policy2'])}"
        )

        return {
            "similarity_score": similarity_score,
            "details": comparison
        }
    except Exception as e:
        logging.error(f"Error in policy comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include all routers
router.include_router(weather_router)
router.include_router(policy_router)
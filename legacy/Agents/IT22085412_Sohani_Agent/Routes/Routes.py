from fastapi import APIRouter, UploadFile, File
from utils import extract_text_from_pdf
from Agent.analyser import analyze_document, summarize_text, extract_entities
from models import PolicyAnalysis

router = APIRouter()

@router.post("/analyze", response_model=PolicyAnalysis)
async def analyze_document_api(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}
    text = extract_text_from_pdf(file.file)
    result = analyze_document(text)
    return result

@router.post("/summarize")
async def summarize_api(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}
    text = extract_text_from_pdf(file.file)
    summary = summarize_text(text)
    return {"summary": summary}

@router.post("/ner")
async def ner_api(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}
    text = extract_text_from_pdf(file.file)
    entities = extract_entities(text)
    return {"entities": entities}

# ----------------------------
# NEW FULL ANALYSIS ENDPOINT
# ----------------------------
@router.post("/full-analysis")
async def full_analysis_api(file: UploadFile = File(...)):
    """
    Upload a PDF and get:
    1. Structured Policy Analysis
    2. Policy Summary
    3. Named Entities
    """
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}

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

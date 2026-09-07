from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from utils.document_processor import process_document
from utils.text_utils import sanitize_text
from utils.document_analyzer import split_into_policies, summarize_text, extract_entities
import logging


policy_router = APIRouter(prefix="/policy", tags=["policy"])

# -------------------------
# 📌 Full Analysis Endpoint
# -------------------------
@policy_router.post("/full-analysis")
async def full_analysis(request: Request, file: UploadFile = File(...)):
    """
    Full pipeline:
    1. Extract + preprocess
    2. Split into Policy A & B
    3. Compare policies
    4. Summaries & Entities
    5. Weather Recommendations
    """
    try:
        # Step 1: Preprocess
        file_bytes = await file.read()
        doc_result = process_document(file_bytes, file.filename)
        clean_text = sanitize_text(doc_result["processed_text"])

        # Step 2: Split & Analyze
        extracted = await split_into_policies(clean_text, request.app.state.nlp)

        # Step 3: Compare policies
        comparator = request.app.state.comparator
        similarity_score = comparator.compute_similarity(
            extracted.policy1.content, extracted.policy2.content
        )
        comparison = comparator.extract_overlap_unique(
            extracted.policy1.content, extracted.policy2.content
        )

        # Step 4: Summaries
        summary1 = await summarize_text(extracted.policy1.content, request.app.state.summarizer)
        summary2 = await summarize_text(extracted.policy2.content, request.app.state.summarizer)

        # Step 5: Entities
        entities = await extract_entities(clean_text, request.app.state.nlp)

        # Step 6: Weather Recommendations (baseline demo)
        rec_engine = request.app.state.weather_processor
        recs = rec_engine.recommend({
            "location": "Colombo",
            "month": 8,
            "temperature_c": 28,
            "humidity_pct": 75,
            "wind_kmh": 12
        })

        # ✅ Flatten response so frontend works directly
        return {
            "status": "success",
            "document_name": doc_result["filename"],
            "statistics": doc_result["statistics"],
            "policies": {
                "policy1": {
                    "content": extracted.policy1.content,
                    "summary": summary1,
                    "keywords": list(extracted.policy1.keywords)
                },
                "policy2": {
                    "content": extracted.policy2.content,
                    "summary": summary2,
                    "keywords": list(extracted.policy2.keywords)
                }
            },
            "similarity_score": similarity_score,
            "details": comparison,
            "entities": entities,
            "recommendations": recs
        }
    except Exception as e:
        logging.error(f"Full analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# 📌 Named Entity Recognition Endpoint
# -------------------------
@policy_router.post("/ner")
async def ner_api(request: Request, file: UploadFile = File(...)):
    """
    Extract named entities (ORG, DATE, GPE, MONEY, etc.)
    from a PDF/DOCX document.
    """
    try:
        # Read file content
        file_bytes = await file.read()
        doc_result = process_document(file_bytes, file.filename)

        # Clean text
        text = sanitize_text(doc_result["processed_text"])

        # Use spaCy model from app.state
        entities = await extract_entities(text, nlp=request.app.state.nlp)

        return {
            "status": "success",
            "filename": doc_result["filename"],
            "entities": entities
        }

    except Exception as e:
        logging.error(f"NER error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# 📌 Summarization Endpoint
# -------------------------
@policy_router.post("/summarize")
async def summarize_api(request: Request, file: UploadFile = File(...)):
    """
    Generate a concise summary of the document.
    """
    try:
        file_bytes = await file.read()
        doc_result = process_document(file_bytes, file.filename)
        text = sanitize_text(doc_result["processed_text"])

        summary = await summarize_text(text, request.app.state.summarizer)

        return {
            "status": "success",
            "filename": doc_result["filename"],
            "summary": summary
        }
    except Exception as e:
        logging.error(f"Summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# 📌 Simple Analysis Endpoint
# -------------------------
@policy_router.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    """
    Extract + preprocess only (lightweight analysis).
    """
    try:
        file_bytes = await file.read()
        doc_result = process_document(file_bytes, file.filename)

        return {
            "status": "success",
            "filename": doc_result["filename"],
            "text": doc_result["processed_text"],
            "statistics": doc_result["statistics"]
        }
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

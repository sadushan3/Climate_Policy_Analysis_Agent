from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import spacy
from Backend.Agents.IT22180520_Sadushan_Agent.utils.Utils import sanitize_text

router = APIRouter()

# Load English language model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

class TextRequest(BaseModel):
    text: str
    type: str = 'document'  # Optional field with default value

@router.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    # Read and process the file
    content = await file.read()
    text = content.decode("utf-8")
    sanitized_text = sanitize_text(text)
    
    return {"text": sanitized_text}

@router.post("/ner")
async def named_entity_recognition(request: TextRequest):
    try:
        if not request.text or not isinstance(request.text, str):
            raise HTTPException(
                status_code=400, 
                detail="Text is required and must be a string"
            )
        
        if len(request.text.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Text cannot be empty"
            )
        
        # Process text with spaCy
        doc = nlp(request.text)
        
        # Extract named entities
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
        
        if not entities:
            return {
                "entities": [],
                "success": True,
                "message": "No entities found in the text"
            }
        
        return {
            "entities": entities,
            "success": True
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error processing text: {str(e)}"
        )

@router.post("/full-analysis")
async def full_analysis(request: TextRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # Process text with spaCy
    doc = nlp(request.text)
    
    # Get entities
    entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    
    # Get key phrases (noun chunks)
    key_phrases = [chunk.text for chunk in doc.noun_chunks]
    
    # Basic statistics
    sentence_count = len(list(doc.sents))
    word_count = len([token for token in doc if not token.is_punct])
    
    return {
        "entities": entities,
        "key_phrases": key_phrases,
        "statistics": {
            "sentence_count": sentence_count,
            "word_count": word_count
        },
        "success": True
    }
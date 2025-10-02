from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.document_processor import process_document
import logging

document_router = APIRouter(prefix="/document", tags=["document"])

@document_router.post("/preprocess")
async def preprocess_document(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        result = process_document(file_bytes, file.filename)

        if not result["processed_text"]:
            raise HTTPException(status_code=400, detail="No text could be extracted")

        return {
            "status": "success",
            "filename": result["filename"],
            "processed_text": result["processed_text"],
            "statistics": result["statistics"]
        }
    except Exception as e:
        logging.error(f"Error in preprocessing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

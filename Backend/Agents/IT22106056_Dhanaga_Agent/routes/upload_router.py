import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
import shutil
import logging

from ..utils.config import settings
from ..pipeline.document_processor import DocumentProcessingPipeline
from ..models.document import (
    Document, 
    DocumentResponse, 
    DocumentListResponse,
    DocumentProcessingOptions
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",  # Remove /api/v1 from here
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

# Initialize document processing pipeline
pipeline = DocumentProcessingPipeline(
    upload_dir=settings.UPLOAD_DIR,
    output_dir=os.path.join(settings.UPLOAD_DIR, 'processed')
)

async def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    """Save an uploaded file to the specified destination."""
    try:
        # Create the directory if it doesn't exist
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file in chunks to handle large files
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return destination
    except Exception as e:
        logger.error(f"Error saving file {upload_file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )

@router.post("/upload/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="The document file to upload (PDF or DOCX)"),
    options: Optional[DocumentProcessingOptions] = None
):
    """
    Upload and process a single document.
    
    Supported file types: PDF, DOCX
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Check file type
    content_type = file.content_type
    if content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {content_type} not supported. Please upload a PDF or DOCX file."
        )
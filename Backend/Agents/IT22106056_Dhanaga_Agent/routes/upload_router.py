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

    try:
        # Generate a unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = Path(settings.UPLOAD_DIR) / unique_filename
        
        # Save the uploaded file
        await save_upload_file(file, file_path)
        
        # Process the document through the pipeline
        document_data = pipeline.process_document(file_path)
        
        # Save the processed document as JSON
        json_path = pipeline.save_as_json(document_data)
        
        # Create response
        response = DocumentResponse(
            success=True,
            message=f"Successfully processed {file.filename}",
            document=Document(**document_data),
            metadata={
                'json_path': str(json_path),
                'original_filename': file.filename
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        # Clean up the file if it was partially uploaded
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.post("/upload/batch/", response_model=List[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_multiple_documents(
    files: List[UploadFile] = File(..., description="Multiple document files to upload (PDF or DOCX)"),
    options: Optional[DocumentProcessingOptions] = None
):
    """
    Upload and process multiple documents in a single request.
    
    Supported file types: PDF, DOCX
    """
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    responses = []
    
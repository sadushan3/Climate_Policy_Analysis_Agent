import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
import shutil
import logging

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

# Local upload directory (relative to this agent)
BASE_DIR = Path(__file__).resolve().parents[2]  # Backend/Agents/
UPLOAD_DIR = BASE_DIR / 'uploads'
PROCESSED_DIR = UPLOAD_DIR / 'processed'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Initialize document processing pipeline
pipeline = DocumentProcessingPipeline(
    upload_dir=str(UPLOAD_DIR),
    output_dir=str(PROCESSED_DIR)
)

async def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    """Save an uploaded file to the specified destination."""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as buffer:
            import shutil
            shutil.copyfileobj(upload_file.file, buffer)
        return destination
    except Exception as e:
        import logging
        from fastapi import HTTPException, status
        logging.getLogger(__name__).error(f"Error saving file {upload_file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )

router = APIRouter(
    prefix="/documents",  # Remove /api/v1 from here
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

@router.post("/upload/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="The document file to upload (PDF only)"),
    options: Optional[DocumentProcessingOptions] = None
):
    """
    Upload and process a single document.
    
    Supported file types: PDF
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Allowed file types
    allowed_exts = {".pdf", ".docx"}
    allowed_mimes = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    # Check file type (PDF or DOCX)
    ext = Path(file.filename).suffix.lower()
    mime = (file.content_type or "").lower()
    if ext not in allowed_exts or mime not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: ext={ext}, mime={mime}. Please upload a PDF or DOCX file."
        )
    

    try:
        # Generate a unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save the uploaded file
        await save_upload_file(file, file_path)
        
        # Process the document
        document_data = pipeline.process_document(file_path)
        
        # Save the processed document as JSON
        json_path = pipeline.save_as_json(document_data)
        
        # Create response
        return DocumentResponse(
            success=True,
            message=f"Successfully processed {file.filename}",
            document=Document(**document_data)
        )
        
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
    files: List[UploadFile] = File(..., description="Multiple document files to upload (PDF only)"),
    options: Optional[DocumentProcessingOptions] = None
):
    """
    Upload and process multiple documents in a single request.
    
    Supported file types: PDF
    """
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    responses = []

    for file in files:
        try:
            # Check file type (PDF or DOCX)
            ext = Path(file.filename).suffix.lower()
            mime = (file.content_type or "").lower()
            allowed_exts = {".pdf", ".docx"}
            allowed_mimes = {
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

            }
            if ext not in allowed_exts or mime not in allowed_mimes:
                responses.append(DocumentResponse(
                    success=False,
                    message=f"Skipped {file.filename}: Unsupported file type",
                    error=f"Unsupported file type: ext={ext}, mime={mime}"
                ))
                continue
            
            # Generate a unique filename
            file_extension = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            # Save the uploaded file
            await save_upload_file(file, file_path)
            
            # Process the document
            document_data = pipeline.process_document(file_path)
            
            # Create response
            responses.append(DocumentResponse(
                success=True,
                message=f"Successfully processed {file.filename}",
                document=Document(**document_data)
            ))

        except Exception as e:
            logger.error(f"Error processing document {file.filename}: {str(e)}")
            # Clean up the file if it was partially uploaded
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
                
            responses.append(DocumentResponse(
                success=False,
                message=f"Failed to process {file.filename}",
                error=str(e)
            ))
    
    return responses
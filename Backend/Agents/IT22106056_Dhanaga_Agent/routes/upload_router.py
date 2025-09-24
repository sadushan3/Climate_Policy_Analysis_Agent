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
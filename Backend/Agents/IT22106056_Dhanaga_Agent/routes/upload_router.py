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
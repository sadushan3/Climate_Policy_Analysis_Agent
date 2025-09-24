import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime
import hashlib

from ..models.document import Document, DocumentMetadata, DocumentSection, DocumentProcessingOptions
from ..utils.document_cleaner import DocumentCleaner

logger = logging.getLogger(__name__)

class DocumentProcessingPipeline:
    """
    Pipeline for processing raw policy documents into structured JSON format.
    Uses DocumentCleaner for comprehensive text cleaning and preprocessing.
    """
    
    def __init__(self, upload_dir: str, output_dir: str):
        """
        Initialize the pipeline with input and output directories.
        
        Args:
            upload_dir: Directory where raw documents are uploaded
            output_dir: Directory to store processed JSON files
        """
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        self.document_cleaner = DocumentCleaner()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
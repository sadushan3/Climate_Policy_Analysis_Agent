"""
Climate Policy Analysis AI - Document Analyzer

This package provides the core functionality for analyzing climate policy documents,
including document upload, text extraction, cleaning, and processing.

Modules:
    - models: Pydantic models for data validation and serialization
    - routers: API endpoint handlers
    - utils: Core processing utilities and helpers
"""

__version__ = '0.1.0'
__author__ = 'Your Name <your.email@example.com>'
__all__ = ['models', 'routers', 'utils']

# Initialize package-level logger
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import key components to make them available at package level
from .models.document import (
    Document,
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    DocumentProcessingOptions
)

# This makes the app directory a Python package

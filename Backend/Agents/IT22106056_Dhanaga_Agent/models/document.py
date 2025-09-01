from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"

class DocumentSection(BaseModel):
    """Represents a section within a document."""
    title: str
    content: str
    start_line: int
    end_line: int

class DocumentMetadata(BaseModel):
    """Metadata extracted from a document."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    page_count: Optional[int] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    file_type: Optional[str] = None

class DocumentBase(BaseModel):
    """Base model for document data."""
    file_name: str
    file_size: int
    file_type: str
    language: Optional[str] = None
    processing_date: datetime = Field(default_factory=datetime.utcnow)

class DocumentCreate(DocumentBase):
    """Model for creating a new document."""
    pass

class Document(DocumentBase):
    """Full document model with all data."""
    id: str
    text: str
    sections: List[DocumentSection] = []
    metadata: DocumentMetadata
    keywords: List[str] = []
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    """API response model for document operations."""
    success: bool
    message: str
    document: Optional[Document] = None
    error: Optional[str] = None

class DocumentListResponse(BaseModel):
    """API response model for listing documents."""
    success: bool
    count: int
    documents: List[Document]

class DocumentProcessRequest(BaseModel):
    """Request model for processing a document."""
    file_path: str
    options: Optional[Dict[str, Any]] = None

class DocumentComparisonRequest(BaseModel):
    """Request model for comparing documents."""
    document_ids: List[str]
    comparison_options: Optional[Dict[str, Any]] = None

class DocumentComparisonResult(BaseModel):
    """Result of comparing multiple documents."""
    common_keywords: List[str]
    unique_keywords: Dict[str, List[str]]
    similarity_score: Optional[float] = None
    comparison_metrics: Dict[str, Any] = {}

class DocumentProcessingOptions(BaseModel):
    """Options for document processing."""
    extract_sections: bool = True
    extract_keywords: bool = True
    detect_language: bool = True
    clean_text: bool = True
    max_keywords: int = 20
    min_section_length: int = 100

import fitz  # PyMuPDF
import docx
import re
from typing import Dict, Any
import logging
from io import BytesIO

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file"""
    doc = docx.Document(BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

def preprocess_text(text: str) -> str:
    """Clean and preprocess extracted text"""
    # Remove extra whitespace and normalize line endings
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove special characters but keep essential punctuation
    text = re.sub(r'[^\w\s.,;?!-]', '', text)
    
    # Split into sentences and recombine with proper spacing
    sentences = re.split(r'([.!?])\s*', text)
    text = ''.join([s.strip() + ' ' for s in sentences]).strip()
    
    return text

def process_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Process document and return structured information"""
    try:
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            raw_text = extract_text_from_pdf(file_bytes)
        elif filename.lower().endswith(('.docx', '.doc')):
            raw_text = extract_text_from_docx(file_bytes)
        else:
            raise ValueError("Unsupported file format")

        # Preprocess the extracted text
        processed_text = preprocess_text(raw_text)

        # Basic document statistics
        word_count = len(processed_text.split())
        sentence_count = len(re.split(r'[.!?]+', processed_text))
        
        return {
            "filename": filename,
            "raw_text": raw_text,
            "processed_text": processed_text,
            "statistics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "average_words_per_sentence": round(word_count / max(1, sentence_count), 2)
            }
        }
        
    except Exception as e:
        logging.error(f"Error processing document {filename}: {str(e)}")
        raise
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

      def process_document(
        self, 
        file_path: Path,
        options: Optional[DocumentProcessingOptions] = None
    ) -> Dict[str, Any]:
        """
        Process a single document through the pipeline.
        
        Args:
            file_path: Path to the document file
            options: Optional processing options
            
        Returns:
            Dictionary containing the processed document data
        """
        if options is None:
            options = DocumentProcessingOptions()
            
        try:
            # Clean and process the document
            cleaned_data = self.document_cleaner.clean_document(file_path)
            
            # Generate a unique document ID
            doc_id = self._generate_document_id(file_path, cleaned_data)
            
            # Get metadata from cleaned data
            metadata = cleaned_data.get('metadata', {})
            metadata.update({
                'title': file_path.stem,
                'file_type': file_path.suffix.lstrip('.').lower() or 'pdf'
            })
            
            # Process document sections with section detection enabled
            options.extract_sections = True  # Ensure section extraction is enabled
            sections = self._process_sections(cleaned_data.get('sections', {}), options)
            
            # Initialize empty keywords list as we're not extracting them
            keywords = []
            
            # Build the document data structure with proper section handling
            document_data = {
                'id': doc_id,
                'file_name': file_path.name,
                'file_size': os.path.getsize(file_path),
                'file_type': metadata.get('file_type', 'pdf'),
                'text': cleaned_data.get('text', ''),
                'sections': [
                    {
                        'title': title if title != 'content' else 'Document Content',
                        'content': content,
                        'start_line': 0,  # These can be updated if line tracking is needed
                        'end_line': len(content.split('\n'))
                    }
                    for title, content in sections.items()
                ] if sections else [
                    {
                        'title': 'Document Content',
                        'content': cleaned_data.get('text', ''),
                        'start_line': 0,
                        'end_line': len(cleaned_data.get('text', '').split('\n'))
                    }
                ],
                'metadata': metadata,
                'keywords': keywords,
                'processing_date': datetime.utcnow().isoformat()
            }
            
            return document_data
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise  

      def _generate_document_id(self, file_path: Path, cleaned_data: Dict[str, Any]) -> str:
        """Generate a unique ID for the document."""
        # Use a combination of file properties and content hash
        content = f"{file_path.name}{file_path.stat().st_size}"
        if 'text' in cleaned_data and len(cleaned_data['text']) > 0:
            content += cleaned_data['text'][:1000]  # Use first 1000 chars for content
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()

      def _process_sections(
        self, 
        sections: Dict[str, str],
        options: DocumentProcessingOptions
    ) -> Dict[str, str]:
        """
        Process document sections with enhanced section detection.
        
        Args:
            sections: Dictionary of sections from the document cleaner
            options: Processing options
            
        Returns:
            Processed sections with improved structure
        """
        if not options.extract_sections:
            return {'content': '\n\n'.join(sections.values())}
            
        # If no sections were detected, return the entire content as one section
        if not sections:
            return {'content': '\n\n'.join(sections.values()) if sections else ''}
            
        # Process each section to clean up titles and content
        processed_sections = {}
        for title, content in sections.items():
            # Clean up section titles
            clean_title = title.strip()
            if not clean_title or clean_title.lower() == 'content':
                clean_title = 'Document Content'
            
            # Clean up section content
            clean_content = content.strip()
            
            # Only include non-empty sections
            if clean_content:
                processed_sections[clean_title] = clean_content
        
        # If we ended up with no valid sections, return the entire content
        if not processed_sections:
            return {'Document Content': '\n\n'.join(sections.values())}
            
        return processed_sections 

      def save_as_json(self, document_data: Dict[str, Any]) -> Path:
        """
        Save the processed document data as a JSON file.
        
        Args:
            document_data: Processed document data
            
        Returns:
            Path to the saved JSON file
        """
        try:
            # Create a filename based on document title or ID
            doc_id = document_data.get('id', 'document')
            output_file = self.output_dir / f"{doc_id}.json"
            
            # Save as pretty-printed JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved processed document to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving document to JSON: {e}")
            raise 

      def process_directory(self, input_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Process all documents in a directory.
        
        Args:
            input_dir: Directory containing documents to process. If None, uses upload_dir.
            
        Returns:
            List of processed document data
        """
        input_dir = Path(input_dir) if input_dir else self.upload_dir
        processed_docs = []
        
        # Process all supported document types
        for ext in ['.pdf', '.docx', '.txt']:
            for doc_file in input_dir.glob(f'*{ext}'):
                try:
                    doc_data = self.process_document(doc_file)
                    self.save_as_json(doc_data)
                    processed_docs.append(doc_data)
                except Exception as e:
                    logger.error(f"Error processing {doc_file}: {e}")
                    continue
                    
        return processed_docs  

      def save_as_json(self, document_data: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """
        Save processed document data as JSON.
        
        Args:
            document_data: Processed document data
            output_path: Optional custom output path
            
        Returns:
            Path to the saved JSON file
        """
        if output_path is None:
            output_path = self.output_dir / f"{document_data['id']}.json"
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(document_data, f, indent=2, ensure_ascii=False)
            
        return output_path  
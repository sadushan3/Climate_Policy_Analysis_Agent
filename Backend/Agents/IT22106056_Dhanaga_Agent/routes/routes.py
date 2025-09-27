from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
import os
import tempfile
from ..Utils.Utils import DocumentProcessor

router = APIRouter()

# Initialize the document processor
doc_processor = DocumentProcessor()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF or DOCX document
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Extract text from document
            extracted_text = doc_processor.extract_text(temp_file_path)
            
            # Clean and preprocess the text
            processed_text = doc_processor.clean_and_preprocess(extracted_text)
            
            # Store the processed document
            doc_id = doc_processor.store_processed_document(
                filename=file.filename,
                original_text=extracted_text,
                processed_text=processed_text
            )
            
            # Automatically send to Document Analyzer Agent via pipeline
            analyzer_response = doc_processor.send_to_analyzer_agent(doc_id)
            
            return JSONResponse(content={
                "message": "Document processed successfully",
                "document_id": doc_id,
                "filename": file.filename,
                "original_length": len(extracted_text),
                "processed_length": len(processed_text),
                "preview": processed_text[:500] + "..." if len(processed_text) > 500 else processed_text,
                "analyzer_pipeline": analyzer_response
            })
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/processed/{document_id}")
async def get_processed_document(document_id: str):
    """
    Retrieve a processed document by ID
    """
    try:
        document = doc_processor.get_processed_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return JSONResponse(content=document)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@router.get("/processed/{document_id}/preview")
async def preview_processed_document(document_id: str, lines: int = 50):
    """
    Get a preview of the processed document (first N lines)
    """
    try:
        document = doc_processor.get_processed_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        processed_lines = document['processed_text'].split('\n')[:lines]
        
        return JSONResponse(content={
            "document_id": document_id,
            "filename": document['filename'],
            "preview_lines": len(processed_lines),
            "total_lines": len(document['processed_text'].split('\n')),
            "preview": '\n'.join(processed_lines)
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document preview: {str(e)}")

@router.get("/processed/{document_id}/download")
async def download_processed_document(document_id: str, format: str = "docx"):
    """
    Download the processed document as DOCX or TXT
    """
    document = doc_processor.get_processed_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    filename_base = os.path.splitext(document['filename'])[0]

    if format.lower() == "docx":
        docx_bytes = doc_processor.build_docx_bytes(document['processed_text'], title=filename_base)
        return StreamingResponse(
            docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename=processed_{filename_base}.docx"
            }
        )
    elif format.lower() == "txt":
        return PlainTextResponse(
            content=document['processed_text'],
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=processed_{filename_base}.txt"
            }
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'docx' or 'txt'.")

@router.post("/send-to-analyzer/{document_id}")
async def send_to_document_analyzer(document_id: str):
    """
    Send processed document to Document Analyzer Agent
    """
    try:
        result = doc_processor.send_to_analyzer_agent(document_id)
        return JSONResponse(content={
            "message": "Document sent to analyzer successfully",
            "document_id": document_id,
            "analyzer_response": result
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending to analyzer: {str(e)}")

@router.get("/documents")
async def list_processed_documents():
    """
    List all processed documents
    """
    try:
        documents = doc_processor.list_documents()
        return JSONResponse(content={"documents": documents})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")
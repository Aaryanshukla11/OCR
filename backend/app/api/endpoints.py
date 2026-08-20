import os
import shutil
import tempfile
import numpy as np
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.core.pipeline import OCRPipeline
from app.validation.validator import ValidationError
from app.services.history import add_history_entry, get_history, clear_history

router = APIRouter()
TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "test-data"))

@router.get("/health")
def health_check():
    pipeline = OCRPipeline.get_instance()
    return {
        "status": "healthy",
        "engine": pipeline.config.engine.name,
        "engine_version": pipeline.config.engine.version,
        "provider": pipeline.model_provider.provider_name,
        "model": "PaddleOCR 3.7.0",
        "device": pipeline.model_provider.device,
    }

@router.post("/ocr")
async def run_ocr(
    file: UploadFile = File(...),
    ground_truth: str = Form(None)
):
    filename = file.filename or "uploaded_file"
    file_bytes = await file.read()
    
    pipeline = OCRPipeline.get_instance()
    
    try:
        # Delegate execution to OCR Pipeline Orchestrator
        doc_result = pipeline.process_file(
            file_bytes=file_bytes,
            filename=filename,
            ground_truth=ground_truth
        )
        
        if isinstance(doc_result, dict):
            response_data = doc_result
            proc = doc_result.get("processing", {})
            doc = doc_result.get("document", {})
            
            add_history_entry(
                filename=filename,
                processing_time=proc.get("processing_time_sec", 0.0),
                total_regions=doc_result.get("total_regions", 0),
                average_confidence=doc_result.get("average_confidence", 0.0),
                device=proc.get("device", "CPU"),
                status="success",
                file_type=doc.get("file_type", "UNKNOWN"),
                pages_count=doc.get("page_count", 1)
            )
            
            response_data["processing_time"] = proc.get("processing_time_sec", 0.0)
            response_data["device"] = proc.get("device", "CPU")
            response_data["filename"] = doc.get("filename", filename)
            response_data["file_type"] = doc.get("file_type", "UNKNOWN")
            response_data["total_pages"] = doc.get("page_count", 1)
        else:
            response_data = doc_result.dict()
            add_history_entry(
                filename=filename,
                processing_time=doc_result.processing.processing_time_sec,
                total_regions=doc_result.total_regions,
                average_confidence=doc_result.average_confidence,
                device=doc_result.processing.device,
                status="success",
                file_type=doc_result.document.file_type,
                pages_count=doc_result.document.page_count
            )
            response_data["processing_time"] = doc_result.processing.processing_time_sec
            response_data["device"] = doc_result.processing.device
            response_data["filename"] = doc_result.document.filename
            response_data["file_type"] = doc_result.document.file_type
            response_data["total_pages"] = doc_result.document.page_count
            
        return JSONResponse(content=response_data)
        
    except ValidationError as ve:
        add_history_entry(
            filename=filename,
            processing_time=0.0,
            total_regions=0,
            average_confidence=0.0,
            device=pipeline.model_provider.device,
            status="failed",
            file_type=filename.split(".")[-1].upper() if "." in filename else "UNKNOWN",
            pages_count=0
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        add_history_entry(
            filename=filename,
            processing_time=0.0,
            total_regions=0,
            average_confidence=0.0,
            device=pipeline.model_provider.device,
            status="failed",
            file_type=filename.split(".")[-1].upper() if "." in filename else "UNKNOWN",
            pages_count=0
        )
        raise HTTPException(
            status_code=500,
            detail=f"OCR Engine processing failed for document '{filename}': {str(e)}"
        )

@router.get("/history")
def get_test_history():
    return get_history()

@router.delete("/history")
def clear_test_history():
    clear_history()
    return {"status": "success", "message": "Test history cleared"}

@router.get("/test-data")
def list_test_categories():
    categories = []
    if os.path.exists(TEST_DATA_DIR):
        folders = sorted([d for d in os.listdir(TEST_DATA_DIR) if os.path.isdir(os.path.join(TEST_DATA_DIR, d))])
        for folder in folders:
            folder_path = os.path.join(TEST_DATA_DIR, folder)
            files = sorted(os.listdir(folder_path))
            image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.pdf'))]
            categories.append({
                "category": folder,
                "files": image_files
            })
    return {"categories": categories}

@router.get("/test-data/{category}/{filename}")
def serve_test_data_file(category: str, filename: str):
    file_path = os.path.abspath(os.path.join(TEST_DATA_DIR, category, filename))
    if not file_path.startswith(TEST_DATA_DIR) or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Test data file not found")
        
    return FileResponse(file_path)

@router.get("/test-data-gt/{category}/{filename}")
def get_ground_truth_content(category: str, filename: str):
    base_filename = os.path.splitext(filename)[0] + ".txt"
    gt_path = os.path.abspath(os.path.join(TEST_DATA_DIR, category, base_filename))
    if not gt_path.startswith(TEST_DATA_DIR) or not os.path.exists(gt_path):
        return {"ground_truth": None}
    with open(gt_path, "r", encoding="utf-8") as f:
        return {"ground_truth": f.read()}

# ==========================================
# Document Intelligence & Query REST APIs
# ==========================================

from pydantic import BaseModel

class QueryApiRequest(BaseModel):
    query: str

@router.get("/documents")
def list_stored_documents(document_type: str = None, search: str = None):
    """Returns stored documents list from SQLite database."""
    from app.services.database import DatabaseService
    docs = DatabaseService.get_documents(document_type=document_type, search_query=search)
    return {"documents": [d.dict() for d in docs]}

@router.get("/documents/{doc_id}")
def get_stored_document_detail(doc_id: str):
    """Retrieves full detailed document intelligence payload from SQLite."""
    from app.services.database import DatabaseService
    doc_detail = DatabaseService.get_document_by_id(doc_id)
    if not doc_detail:
        raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found")
    return doc_detail

@router.delete("/documents/{doc_id}")
def delete_stored_document(doc_id: str):
    """Deletes stored document from SQLite database."""
    from app.services.database import DatabaseService
    success = DatabaseService.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found")
    return {"status": "success", "message": f"Document '{doc_id}' deleted successfully"}

@router.post("/query")
def execute_natural_language_query(payload: QueryApiRequest):
    """Translates user natural language question into structured query plan & executes SQL search."""
    from app.services.query_engine import DocumentQueryEngine
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty")
        
    response = DocumentQueryEngine.execute_query(payload.query)
    return response.dict()


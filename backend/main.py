"""FastAPI backend for document extraction"""
import os
import uuid
import io
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional, List
import duckdb

from .database import (
    init_database,
    save_extraction,
    get_extraction,
    check_duplicate,
    list_extractions,
    export_to_csv,
    generate_doc_hash
)
from .extraction import extract_document
from .models import ExtractedData


app = FastAPI(title="DocuExtract AI", version="0.1.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
db_conn = None


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    global db_conn
    db_conn = init_database()
    print("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    global db_conn
    if db_conn:
        db_conn.close()


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "ok",
        "ollama_available": False
    }
    
    # Check Ollama availability
    try:
        import ollama
        models = ollama.list()
        status["ollama_available"] = any(
            "qwen3-vl" in model.get("name", "") or "qwen2-vl" in model.get("name", "") 
            for model in models.get("models", [])
        )
    except Exception:
        pass
    
    return status


@app.post("/api/extract")
async def extract_endpoint(file: UploadFile = File(...)):
    """Extract data from uploaded document"""
    global db_conn
    
    # Validate file type
    allowed_types = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/gif",
        "image/webp"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Read file bytes
    file_bytes = await file.read()
    
    # Check file size (10MB limit)
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )
    
    # Check for duplicates
    doc_hash = generate_doc_hash(file_bytes)
    existing = check_duplicate(db_conn, doc_hash)
    if existing:
        return {
            "id": existing["id"],
            "data": existing,
            "duplicate": True
        }
    
    # Extract data using local Ollama
    try:
        result = await extract_document(file_bytes, file.filename)
        extracted_data = result["data"]
        confidence = result["confidence"]
        provider = result["provider"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )
    
    # Save to database
    extraction_id = str(uuid.uuid4())
    try:
        save_extraction(
            db_conn,
            extraction_id,
            doc_hash,
            file.filename,
            extracted_data,
            confidence
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save extraction: {str(e)}"
        )
    
    return {
        "id": extraction_id,
        "data": extracted_data,
        "confidence": confidence,
        "provider": provider,
        "duplicate": False
    }


@app.get("/api/extractions")
async def list_extractions_endpoint(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    vendor: Optional[str] = Query(None, description="Filter by vendor name"),
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List extractions with filters and pagination"""
    global db_conn
    
    extractions, total = list_extractions(
        db_conn,
        date_from=date_from,
        date_to=date_to,
        vendor=vendor,
        doc_type=doc_type,
        offset=offset,
        limit=limit
    )
    
    return {
        "extractions": extractions,
        "total": total,
        "offset": offset,
        "limit": limit
    }


@app.get("/api/extractions/export")
async def export_extractions_endpoint(
    extraction_ids: Optional[str] = Query(None, description="Comma-separated extraction IDs"),
    format: str = Query("csv", pattern="^(csv|parquet)$")
):
    """Export extractions to CSV or Parquet"""
    global db_conn
    
    ids = None
    if extraction_ids:
        ids = [id.strip() for id in extraction_ids.split(",")]
    
    if format == "csv":
        csv_bytes = export_to_csv(db_conn, ids)
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=extractions.csv"}
        )
    else:
        raise HTTPException(status_code=400, detail="Parquet export not yet implemented")


@app.get("/api/extractions/{extraction_id}")
async def get_extraction_endpoint(extraction_id: str):
    """Get single extraction by ID"""
    global db_conn
    
    extraction = get_extraction(db_conn, extraction_id)
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
    
    return extraction


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

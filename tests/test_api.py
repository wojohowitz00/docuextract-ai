"""Tests for FastAPI endpoints"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, Mock
import tempfile
import os


@pytest.fixture
def client():
    """Create test client"""
    import backend.main
    # Mock database initialization
    mock_conn = Mock()
    backend.main.db_conn = mock_conn
    
    # Mock database functions
    with patch("backend.main.init_database", return_value=mock_conn):
        yield TestClient(app)
    
    # Cleanup
    backend.main.db_conn = None


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for upload"""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
179
%%EOF"""
    return ("test.pdf", pdf_content, "application/pdf")


@pytest.fixture
def sample_image_file():
    """Create a sample image file for upload"""
    png_content = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00'
        b'\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return ("test.png", png_content, "image/png")


def test_health_check(client):
    """Test health check endpoint"""
    import ollama
    with patch.object(ollama, "list", return_value={"models": [{"name": "qwen3-vl"}]}):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert isinstance(data["ollama_available"], bool)
        assert isinstance(data["gemini_available"], bool)


def test_extract_endpoint_success(client, sample_pdf_file):
    """Test successful extraction endpoint"""
    filename, content, content_type = sample_pdf_file
    
    mock_result = {
        "data": {
            "documentType": "Invoice",
            "vendorName": "Test Vendor",
            "totalAmount": 100.0,
            "date": "2024-01-15",
            "invoiceNumber": "INV-001",
            "taxAmount": 10.0,
            "currency": "USD",
            "lineItems": []
        },
        "confidence": 0.9,
        "provider": "ollama"
    }
    
    with patch("backend.main.extract_document", return_value=mock_result):
        with patch("backend.main.save_extraction"):
            with patch("backend.main.check_duplicate", return_value=None):
                files = {"file": (filename, content, content_type)}
                response = client.post("/api/extract", files=files)
                
                assert response.status_code == 200
                data = response.json()
                assert "id" in data
                assert data["data"]["vendorName"] == "Test Vendor"
                assert data["provider"] == "ollama"


def test_extract_endpoint_invalid_file_type(client):
    """Test extraction endpoint with invalid file type"""
    files = {"file": ("test.txt", b"text content", "text/plain")}
    response = client.post("/api/extract", files=files)
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_extract_endpoint_file_too_large(client):
    """Test extraction endpoint with file too large"""
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {"file": ("test.pdf", large_content, "application/pdf")}
    response = client.post("/api/extract", files=files)
    
    assert response.status_code == 400
    assert "10MB" in response.json()["detail"]


def test_extract_endpoint_duplicate(client, sample_pdf_file):
    """Test extraction endpoint with duplicate document"""
    filename, content, content_type = sample_pdf_file
    
    existing_extraction = {
        "id": "existing-id",
        "vendorName": "Existing Vendor"
    }
    
    with patch("backend.main.check_duplicate", return_value=existing_extraction):
        files = {"file": (filename, content, content_type)}
        response = client.post("/api/extract", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["duplicate"] is True
        assert data["id"] == "existing-id"


def test_list_extractions_endpoint(client):
    """Test list extractions endpoint"""
    mock_extractions = [
        {
            "id": "1",
            "filename": "test1.pdf",
            "documentType": "Invoice",
            "vendorName": "Vendor 1",
            "totalAmount": 100.0,
            "currency": "USD",
            "date": "2024-01-15",
            "createdAt": "2024-01-15T10:00:00"
        }
    ]
    
    with patch("backend.main.list_extractions", return_value=(mock_extractions, 1)):
        response = client.get("/api/extractions")
        
        assert response.status_code == 200
        data = response.json()
        assert "extractions" in data
        assert "total" in data
        assert len(data["extractions"]) == 1


def test_list_extractions_with_filters(client):
    """Test list extractions endpoint with filters"""
    with patch("backend.main.list_extractions", return_value=([], 0)):
        response = client.get("/api/extractions?vendor=Test&date_from=2024-01-01")
        
        assert response.status_code == 200


def test_get_extraction_endpoint(client):
    """Test get single extraction endpoint"""
    mock_extraction = {
        "id": "test-id",
        "vendorName": "Test Vendor",
        "totalAmount": 100.0
    }
    
    with patch("backend.main.get_extraction", return_value=mock_extraction):
        response = client.get("/api/extractions/test-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-id"
        assert data["vendorName"] == "Test Vendor"


def test_get_extraction_not_found(client):
    """Test get extraction endpoint with non-existent ID"""
    with patch("backend.main.get_extraction", return_value=None):
        response = client.get("/api/extractions/non-existent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_export_extractions_endpoint(client):
    """Test export extractions endpoint"""
    import backend.main
    import backend.database as db_module
    
    csv_content = b"id,filename,vendor\n1,test.pdf,Vendor 1\n"
    
    # Create real database connection
    db_conn = db_module.init_database()
    backend.main.db_conn = db_conn
    
    # Mock export_to_csv to return test data
    original_func = db_module.export_to_csv
    db_module.export_to_csv = Mock(return_value=csv_content)
    backend.main.export_to_csv = Mock(return_value=csv_content)
    
    try:
        response = client.get("/api/extractions/export?format=csv")
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
    finally:
        db_module.export_to_csv = original_func
        backend.main.export_to_csv = original_func
        if db_conn:
            db_conn.close()


def test_export_extractions_with_ids(client):
    """Test export extractions endpoint with specific IDs"""
    import backend.main
    import backend.database as db_module
    
    csv_content = b"id,filename\n1,test.pdf\n"
    
    # Create real database connection
    db_conn = db_module.init_database()
    backend.main.db_conn = db_conn
    
    # Mock export function
    original_func = db_module.export_to_csv
    db_module.export_to_csv = Mock(return_value=csv_content)
    backend.main.export_to_csv = Mock(return_value=csv_content)
    
    try:
        response = client.get("/api/extractions/export?format=csv&extraction_ids=1,2")
        
        assert response.status_code == 200
    finally:
        db_module.export_to_csv = original_func
        backend.main.export_to_csv = original_func
        if db_conn:
            db_conn.close()

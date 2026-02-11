"""Pytest configuration and fixtures"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import duckdb
from backend.database import init_database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_extractions.duckdb"
    
    # Change to temp directory temporarily
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        conn = init_database()
        yield conn
    finally:
        conn.close()
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_extraction_data():
    """Sample extraction data for testing"""
    return {
        "documentType": "Invoice",
        "vendorName": "Test Vendor Inc.",
        "vendorAddress": "123 Test St, Test City, TC 12345",
        "invoiceNumber": "INV-2024-001",
        "date": "2024-01-15",
        "dueDate": "2024-02-15",
        "totalAmount": 1500.00,
        "taxAmount": 150.00,
        "currency": "USD",
        "lineItems": [
            {
                "description": "Test Product 1",
                "quantity": 2.0,
                "unitPrice": 500.00,
                "total": 1000.00,
                "sku": "SKU-001"
            },
            {
                "description": "Test Product 2",
                "quantity": 1.0,
                "unitPrice": 500.00,
                "total": 500.00,
                "sku": "SKU-002"
            }
        ],
        "summary": "Test invoice for testing purposes"
    }


@pytest.fixture
def sample_pdf_bytes():
    """Create a minimal PDF for testing"""
    # Minimal valid PDF structure
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
    return pdf_content


@pytest.fixture
def sample_image_bytes():
    """Create a minimal PNG image for testing"""
    # Minimal valid PNG (1x1 transparent pixel)
    png_content = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00'
        b'\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return png_content

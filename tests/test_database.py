"""Tests for database module"""
import pytest
import uuid
from backend.database import (
    save_extraction,
    get_extraction,
    check_duplicate,
    list_extractions,
    export_to_csv,
    generate_doc_hash
)


def test_generate_doc_hash():
    """Test document hash generation"""
    file_bytes = b"test document content"
    hash1 = generate_doc_hash(file_bytes)
    hash2 = generate_doc_hash(file_bytes)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
    assert isinstance(hash1, str)


def test_save_extraction(temp_db, sample_extraction_data):
    """Test saving extraction to database"""
    extraction_id = str(uuid.uuid4())
    doc_hash = generate_doc_hash(b"test file")
    filename = "test_invoice.pdf"
    
    result_id = save_extraction(
        temp_db,
        extraction_id,
        doc_hash,
        filename,
        sample_extraction_data,
        confidence=0.95
    )
    
    assert result_id == extraction_id
    
    # Verify extraction was saved
    extraction = get_extraction(temp_db, extraction_id)
    assert extraction is not None
    assert extraction["vendorName"] == "Test Vendor Inc."
    assert extraction["totalAmount"] == 1500.00
    assert len(extraction["lineItems"]) == 2


def test_get_extraction(temp_db, sample_extraction_data):
    """Test retrieving extraction from database"""
    extraction_id = str(uuid.uuid4())
    doc_hash = generate_doc_hash(b"test file")
    
    save_extraction(
        temp_db,
        extraction_id,
        doc_hash,
        "test.pdf",
        sample_extraction_data,
        confidence=0.9
    )
    
    extraction = get_extraction(temp_db, extraction_id)
    
    assert extraction is not None
    assert extraction["documentType"] == "Invoice"
    assert extraction["vendorName"] == "Test Vendor Inc."
    assert extraction["invoiceNumber"] == "INV-2024-001"
    assert extraction["totalAmount"] == 1500.00
    assert extraction["taxAmount"] == 150.00
    assert extraction["currency"] == "USD"
    assert len(extraction["lineItems"]) == 2
    assert extraction["lineItems"][0]["description"] == "Test Product 1"
    assert extraction["lineItems"][0]["quantity"] == 2.0


def test_get_extraction_not_found(temp_db):
    """Test retrieving non-existent extraction"""
    extraction = get_extraction(temp_db, "non-existent-id")
    assert extraction is None


def test_check_duplicate(temp_db, sample_extraction_data):
    """Test duplicate detection"""
    doc_hash = generate_doc_hash(b"duplicate test")
    extraction_id1 = str(uuid.uuid4())
    
    # Save first extraction
    save_extraction(
        temp_db,
        extraction_id1,
        doc_hash,
        "file1.pdf",
        sample_extraction_data,
        confidence=0.9
    )
    
    # Check for duplicate
    existing = check_duplicate(temp_db, doc_hash)
    assert existing is not None
    assert existing["id"] == extraction_id1
    
    # Check with different hash
    different_hash = generate_doc_hash(b"different content")
    assert check_duplicate(temp_db, different_hash) is None


def test_list_extractions(temp_db, sample_extraction_data):
    """Test listing extractions with filters"""
    # Create multiple extractions
    for i in range(5):
        extraction_id = str(uuid.uuid4())
        doc_hash = generate_doc_hash(f"file{i}".encode())
        data = sample_extraction_data.copy()
        data["invoiceNumber"] = f"INV-{i:03d}"
        data["date"] = f"2024-01-{15+i:02d}"
        
        save_extraction(
            temp_db,
            extraction_id,
            doc_hash,
            f"file{i}.pdf",
            data,
            confidence=0.9
        )
    
    # List all
    extractions, total = list_extractions(temp_db)
    assert total == 5
    assert len(extractions) == 5
    
    # Test pagination
    extractions, total = list_extractions(temp_db, offset=2, limit=2)
    assert total == 5
    assert len(extractions) == 2
    
    # Test vendor filter
    extractions, total = list_extractions(temp_db, vendor="Test Vendor")
    assert total == 5
    
    # Test date filter
    extractions, total = list_extractions(temp_db, date_from="2024-01-15", date_to="2024-01-16")
    assert total >= 2
    
    # Test document type filter
    extractions, total = list_extractions(temp_db, doc_type="Invoice")
    assert total == 5


def test_export_to_csv(temp_db, sample_extraction_data):
    """Test CSV export functionality"""
    # Create test extractions
    extraction_ids = []
    for i in range(3):
        extraction_id = str(uuid.uuid4())
        extraction_ids.append(extraction_id)
        doc_hash = generate_doc_hash(f"file{i}".encode())
        data = sample_extraction_data.copy()
        data["invoiceNumber"] = f"INV-{i:03d}"
        
        save_extraction(
            temp_db,
            extraction_id,
            doc_hash,
            f"file{i}.pdf",
            data,
            confidence=0.9
        )
    
    # Export specific extractions
    csv_bytes = export_to_csv(temp_db, extraction_ids[:2])
    csv_text = csv_bytes.decode("utf-8")
    
    assert "id,filename,document_type" in csv_text
    assert "INV-000" in csv_text
    assert "INV-001" in csv_text
    assert "Test Vendor Inc." in csv_text
    
    # Export all
    csv_bytes_all = export_to_csv(temp_db)
    csv_text_all = csv_bytes_all.decode("utf-8")
    assert "INV-002" in csv_text_all

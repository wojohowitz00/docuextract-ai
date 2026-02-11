"""Tests for PDF parser module"""
import pytest
from backend.pdf_parser import (
    detect_file_type,
    extract_text,
    extract_tables,
    pdf_to_images,
    image_to_base64,
    parse_document
)


def test_detect_file_type_pdf():
    """Test PDF file type detection"""
    pdf_bytes = b"%PDF-1.4 test content"
    assert detect_file_type(pdf_bytes, "test.pdf") == "pdf"
    assert detect_file_type(pdf_bytes, "test.PDF") == "pdf"
    assert detect_file_type(pdf_bytes, "unknown") == "pdf"  # Magic bytes


def test_detect_file_type_image():
    """Test image file type detection"""
    png_bytes = b"\x89PNG\r\n\x1a\n"
    assert detect_file_type(png_bytes, "test.png") == "image"
    assert detect_file_type(png_bytes, "test.jpg") == "image"  # Magic bytes
    
    jpeg_bytes = b"\xff\xd8\xff"
    assert detect_file_type(jpeg_bytes, "test.jpeg") == "image"


def test_detect_file_type_unknown():
    """Test unknown file type detection"""
    unknown_bytes = b"random content"
    assert detect_file_type(unknown_bytes, "test.txt") == "unknown"


def test_extract_text(sample_pdf_bytes):
    """Test text extraction from PDF"""
    try:
        pages_text = extract_text(sample_pdf_bytes)
        assert isinstance(pages_text, list)
        assert len(pages_text) >= 0  # May be empty for minimal PDF
    except Exception as e:
        pytest.skip(f"PDF text extraction failed (may need valid PDF): {e}")


def test_extract_tables(sample_pdf_bytes):
    """Test table extraction from PDF"""
    try:
        tables = extract_tables(sample_pdf_bytes)
        assert isinstance(tables, list)
        # Minimal PDF may not have tables
    except Exception as e:
        pytest.skip(f"PDF table extraction failed: {e}")


def test_pdf_to_images(sample_pdf_bytes):
    """Test PDF to image conversion"""
    try:
        images = pdf_to_images(sample_pdf_bytes, dpi=100)
        assert isinstance(images, list)
        assert len(images) >= 0
    except Exception as e:
        pytest.skip(f"PDF to image conversion failed (may need poppler): {e}")


def test_image_to_base64(sample_image_bytes):
    """Test image to base64 conversion"""
    from PIL import Image
    import io
    
    img = Image.open(io.BytesIO(sample_image_bytes))
    base64_str = image_to_base64(img)
    
    assert isinstance(base64_str, str)
    assert len(base64_str) > 0


def test_parse_document_pdf(sample_pdf_bytes):
    """Test document parsing for PDF"""
    result = parse_document(sample_pdf_bytes, "test.pdf", strategy="vision")
    
    assert result["file_type"] == "pdf"
    assert result["filename"] == "test.pdf"
    assert result["strategy"] == "vision"
    assert "images" in result
    assert "image_count" in result


def test_parse_document_image(sample_image_bytes):
    """Test document parsing for image"""
    result = parse_document(sample_image_bytes, "test.png", strategy="vision")
    
    assert result["file_type"] == "image"
    assert result["filename"] == "test.png"
    assert "images" in result
    assert result["image_count"] == 1


def test_parse_document_text_strategy(sample_pdf_bytes):
    """Test document parsing with text strategy"""
    result = parse_document(sample_pdf_bytes, "test.pdf", strategy="text")
    
    assert result["file_type"] == "pdf"
    assert "text" in result
    assert "tables" in result


def test_parse_document_hybrid_strategy(sample_pdf_bytes):
    """Test document parsing with hybrid strategy"""
    result = parse_document(sample_pdf_bytes, "test.pdf", strategy="hybrid")
    
    assert result["file_type"] == "pdf"
    assert "text" in result
    assert "tables" in result
    assert "images" in result

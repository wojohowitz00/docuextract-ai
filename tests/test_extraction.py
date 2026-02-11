"""Tests for extraction module"""
import pytest
import base64
from unittest.mock import Mock, patch, AsyncMock
from backend.extraction import (
    calculate_confidence,
    parse_json_response,
    ollama_extract,
    extract_document
)


def test_calculate_confidence_complete():
    """Test confidence calculation with all required fields"""
    data = {
        "vendorName": "Test Vendor",
        "totalAmount": 100.0,
        "date": "2024-01-15",
        "invoiceNumber": "INV-001",
        "lineItems": [{"description": "Item 1"}]
    }
    
    confidence = calculate_confidence(data)
    assert confidence == 1.0


def test_calculate_confidence_partial():
    """Test confidence calculation with partial fields"""
    data = {
        "vendorName": "Test Vendor",
        "totalAmount": 100.0,
        # Missing date
    }
    
    confidence = calculate_confidence(data)
    assert 0.0 < confidence < 1.0
    assert confidence == pytest.approx(2/3, abs=0.1)


def test_calculate_confidence_minimal():
    """Test confidence calculation with minimal fields"""
    data = {
        "vendorName": "Test Vendor"
    }
    
    confidence = calculate_confidence(data)
    assert confidence == pytest.approx(1/3, abs=0.1)


def test_parse_json_response_clean():
    """Test parsing clean JSON response"""
    json_text = '{"vendorName": "Test", "totalAmount": 100}'
    result = parse_json_response(json_text)
    
    assert result["vendorName"] == "Test"
    assert result["totalAmount"] == 100


def test_parse_json_response_with_markdown():
    """Test parsing JSON response with markdown code blocks"""
    json_text = '```json\n{"vendorName": "Test", "totalAmount": 100}\n```'
    result = parse_json_response(json_text)
    
    assert result["vendorName"] == "Test"
    assert result["totalAmount"] == 100


def test_parse_json_response_with_text():
    """Test parsing JSON response with surrounding text"""
    json_text = 'Some text before {"vendorName": "Test", "totalAmount": 100} and after'
    result = parse_json_response(json_text)
    
    assert result["vendorName"] == "Test"
    assert result["totalAmount"] == 100


def test_parse_json_response_invalid():
    """Test parsing invalid JSON raises error"""
    with pytest.raises(ValueError):
        parse_json_response("not valid json")


@pytest.mark.asyncio
async def test_ollama_extract_success():
    """Test successful Ollama extraction"""
    images = [base64.b64encode(b"fake image").decode("utf-8")]
    mock_response = {
        "message": {
            "content": '{"documentType": "Invoice", "vendorName": "Test", "totalAmount": 100, "date": "2024-01-15"}'
        }
    }
    
    with patch("backend.extraction.ollama.chat", return_value=mock_response):
        result = await ollama_extract(images)
        
        assert result["provider"] == "ollama"
        assert result["confidence"] > 0
        assert result["data"]["vendorName"] == "Test"


@pytest.mark.asyncio
async def test_ollama_extract_failure():
    """Test Ollama extraction failure"""
    images = [base64.b64encode(b"fake image").decode("utf-8")]
    
    with patch("backend.extraction.ollama.chat", side_effect=Exception("Connection error")):
        with pytest.raises(ValueError, match="Ollama extraction failed"):
            await ollama_extract(images)


@pytest.mark.asyncio
async def test_extract_document_ollama_success():
    """Test document extraction with Ollama"""
    file_bytes = b"fake pdf content"
    filename = "test.pdf"
    
    mock_parsed = {
        "file_type": "pdf",
        "images": [base64.b64encode(b"fake image").decode("utf-8")],
        "image_count": 1
    }
    
    mock_ollama_result = {
        "data": {
            "documentType": "Invoice",
            "vendorName": "Test",
            "totalAmount": 100,
            "date": "2024-01-15"
        },
        "confidence": 0.9,
        "provider": "ollama"
    }
    
    with patch("backend.pdf_parser.parse_document", return_value=mock_parsed):
        with patch("backend.extraction.ollama_extract", return_value=mock_ollama_result):
            result = await extract_document(file_bytes, filename)
            
            assert result["provider"] == "ollama"
            assert result["confidence"] == 0.9

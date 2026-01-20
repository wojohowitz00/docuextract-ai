"""Tests for Pydantic models"""
import pytest
from backend.models import DocumentType, LineItem, ExtractedData


def test_document_type_enum():
    """Test DocumentType enum"""
    assert DocumentType.INVOICE == "Invoice"
    assert DocumentType.RECEIPT == "Receipt"
    assert DocumentType.BANK_STATEMENT == "Bank Statement"
    assert DocumentType.INSURANCE_EOB == "Insurance EOB"
    assert DocumentType.UNKNOWN == "Unknown"


def test_line_item_model():
    """Test LineItem model"""
    item = LineItem(
        description="Test Item",
        quantity=2.0,
        unitPrice=10.0,
        total=20.0,
        sku="SKU-001"
    )
    
    assert item.description == "Test Item"
    assert item.quantity == 2.0
    assert item.unitPrice == 10.0
    assert item.total == 20.0
    assert item.sku == "SKU-001"


def test_line_item_model_optional_sku():
    """Test LineItem model without SKU"""
    item = LineItem(
        description="Test Item",
        quantity=1.0,
        unitPrice=10.0,
        total=10.0
    )
    
    assert item.sku is None


def test_extracted_data_model():
    """Test ExtractedData model"""
    data = ExtractedData(
        documentType=DocumentType.INVOICE,
        vendorName="Test Vendor",
        vendorAddress="123 Test St",
        invoiceNumber="INV-001",
        date="2024-01-15",
        dueDate="2024-02-15",
        totalAmount=100.0,
        taxAmount=10.0,
        currency="USD",
        lineItems=[
            LineItem(
                description="Item 1",
                quantity=1.0,
                unitPrice=100.0,
                total=100.0
            )
        ],
        summary="Test invoice"
    )
    
    assert data.documentType == DocumentType.INVOICE
    assert data.vendorName == "Test Vendor"
    assert data.totalAmount == 100.0
    assert len(data.lineItems) == 1


def test_extracted_data_model_minimal():
    """Test ExtractedData model with minimal fields"""
    data = ExtractedData(
        documentType=DocumentType.RECEIPT,
        vendorName="Test Vendor",
        invoiceNumber="",
        date="2024-01-15",
        totalAmount=50.0,
        taxAmount=0.0,
        currency="USD",
        lineItems=[]
    )
    
    assert data.vendorAddress is None
    assert data.dueDate is None
    assert data.summary is None
    assert len(data.lineItems) == 0

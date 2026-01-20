"""Pydantic models matching TypeScript types"""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date


class DocumentType(str, Enum):
    INVOICE = "Invoice"
    RECEIPT = "Receipt"
    BANK_STATEMENT = "Bank Statement"
    INSURANCE_EOB = "Insurance EOB"
    UNKNOWN = "Unknown"


class LineItem(BaseModel):
    description: str
    quantity: float
    unitPrice: float = Field(alias="unitPrice")
    total: float
    sku: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ExtractedData(BaseModel):
    documentType: DocumentType
    vendorName: str
    vendorAddress: Optional[str] = None
    invoiceNumber: str
    date: str  # YYYY-MM-DD format
    dueDate: Optional[str] = None
    totalAmount: float
    taxAmount: float
    currency: str = "USD"
    lineItems: List[LineItem] = []
    summary: Optional[str] = None

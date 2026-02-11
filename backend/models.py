"""Pydantic models for document extraction"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import date


class DocumentType(str, Enum):
    INVOICE = "Invoice"
    RECEIPT = "Receipt"
    BILL = "Bill"
    BANK_STATEMENT = "Bank Statement"
    INSURANCE_EOB = "Insurance EOB"
    RESEARCH_PAPER = "Research Paper"
    FINANCIAL_REPORT = "Financial Report"
    UNKNOWN = "Unknown"


class LineItem(BaseModel):
    description: str
    quantity: float = 0
    unitPrice: float = Field(0, alias="unitPrice")
    total: float = 0
    sku: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ExtractedData(BaseModel):
    """Unified extraction model. Fields are populated based on documentType."""
    documentType: DocumentType

    # --- Common fields ---
    date: Optional[str] = None       # YYYY-MM-DD
    summary: Optional[str] = None    # 1-sentence summary

    # --- Financial document fields (Invoice, Receipt, Bill, Bank Statement, EOB) ---
    vendorName: Optional[str] = None
    vendorAddress: Optional[str] = None
    invoiceNumber: Optional[str] = None
    dueDate: Optional[str] = None
    totalAmount: Optional[float] = None
    taxAmount: Optional[float] = None
    currency: Optional[str] = "USD"
    lineItems: List[LineItem] = []
    accountNumber: Optional[str] = None
    billingPeriod: Optional[str] = None

    # --- Research paper fields ---
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    publicationDate: Optional[str] = None
    keywords: Optional[List[str]] = None
    methodology: Optional[str] = None
    findings: Optional[str] = None

    # --- Financial report fields ---
    companyName: Optional[str] = None
    reportType: Optional[str] = None
    reportPeriod: Optional[str] = None
    revenue: Optional[float] = None
    expenses: Optional[float] = None
    netIncome: Optional[float] = None
    keyMetrics: Optional[Dict[str, Any]] = None

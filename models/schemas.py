"""Pydantic models for EOB data structures."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """Individual service line item within a claim."""
    line_number: int
    service_date: Optional[str] = None
    service_description: Optional[str] = None
    procedure_code: Optional[str] = None
    reason_code: Optional[str] = None
    reason_description: Optional[str] = None
    billed_amount: Optional[float] = None
    allowed_amount: Optional[float] = None
    insurance_paid: Optional[float] = None
    copay: Optional[float] = 0.0
    deductible_applied: Optional[float] = 0.0
    coinsurance: Optional[float] = 0.0
    not_covered: Optional[float] = 0.0
    patient_responsibility: Optional[float] = None


class Accumulator(BaseModel):
    """Deductible or out-of-pocket maximum snapshot."""
    member_name: Optional[str] = None
    coverage_tier: str  # individual | family
    network_type: str   # in_network | out_of_network
    accumulator_type: str  # deductible | oop_max
    limit_amount: Optional[float] = None
    applied_amount: Optional[float] = None
    remaining_amount: Optional[float] = None


class Member(BaseModel):
    """Person covered under the insurance plan."""
    member_id: str
    member_name: str
    relationship: Optional[str] = None  # self, spouse, child, etc.
    first_seen_date: Optional[str] = None


class Document(BaseModel):
    """EOB document metadata."""
    document_id: str
    statement_date: Optional[str] = None
    member_id: Optional[str] = None
    group_id: Optional[str] = None
    source_file: str
    model_used: str = ""
    extracted_at: str = ""


class Claim(BaseModel):
    """Claim-level aggregates."""
    claim_id: str
    document_id: Optional[str] = None
    member_id: Optional[str] = None
    provider_name: Optional[str] = None
    service_date: Optional[str] = None
    claim_received_date: Optional[str] = None
    in_network: Optional[bool] = True
    total_billed: Optional[float] = None
    total_allowed: Optional[float] = None
    total_insurance_paid: Optional[float] = None
    total_patient_responsibility: Optional[float] = None
    claim_status: Optional[str] = "processed"


class EOBExtraction(BaseModel):
    """Full extraction result from one EOB document."""
    # Document metadata
    source_file: str
    statement_date: Optional[str] = None
    member_name: Optional[str] = None
    member_id: Optional[str] = None
    group_id: Optional[str] = None
    
    # Claim info
    claim_number: Optional[str] = None
    provider_name: Optional[str] = None
    service_date: Optional[str] = None
    claim_received_date: Optional[str] = None
    in_network: Optional[bool] = True
    
    # Claim totals
    total_billed: Optional[float] = None
    total_allowed: Optional[float] = None
    total_insurance_paid: Optional[float] = None
    total_patient_responsibility: Optional[float] = None
    
    # Details
    line_items: list[LineItem] = Field(default_factory=list)
    accumulators: list[Accumulator] = Field(default_factory=list)
    
    # Extraction metadata
    model_used: str = ""
    extracted_at: str = ""
    raw_output: str = ""


# Extraction response models for each page type

class Page1Summary(BaseModel):
    """Extracted data from page 1 (summary page)."""
    statement_date: Optional[str] = None
    member_name: Optional[str] = None
    member_id: Optional[str] = None
    group_id: Optional[str] = None
    total_billed: Optional[float] = None
    total_discount: Optional[float] = None
    total_allowed: Optional[float] = None
    total_insurance_paid: Optional[float] = None
    total_you_pay: Optional[float] = None


class Page2Accumulators(BaseModel):
    """Extracted data from page 2 (accumulator page - landscape)."""
    accumulators: list[Accumulator] = Field(default_factory=list)


class Page3Claims(BaseModel):
    """Extracted data from page 3+ (claims details)."""
    claim_number: Optional[str] = None
    provider_name: Optional[str] = None
    service_date: Optional[str] = None
    claim_received_date: Optional[str] = None
    in_network: Optional[bool] = True
    line_items: list[LineItem] = Field(default_factory=list)

"""
Two-model extraction pipeline: DeepSeek OCR2 → Qwen3 30B-A3B

Stage 1: DeepSeek OCR2 converts document images to clean markdown text
Stage 2: Qwen3 (text-only) classifies the document type from markdown
Stage 3: Qwen3 (text-only) extracts structured JSON using type-specific prompts
"""
import json
from typing import Dict, Any, List
import ollama
from .models import DocumentType


# ── Model configuration ───────────────────────────────────────────────────────

OCR_MODEL = "deepseek-ocr"       # Vision → markdown (OCR specialist)
REASONING_MODEL = "qwen3"        # Text → structured JSON (reasoning specialist)


# ── Stage 1: OCR prompt ───────────────────────────────────────────────────────

OCR_PROMPT = """Convert this document image to clean markdown text.
Preserve the full structure: headings, tables, lists, columns, and reading order.
Output ONLY the markdown content. No commentary or explanations."""


# ── Stage 2: Classification prompt (text-only) ────────────────────────────────

CLASSIFICATION_PROMPT = """Below is the text content of a document. Determine what type of document it is.

Respond with ONLY one of these exact strings (no other text, no thinking):
- Invoice
- Receipt
- Bill
- Bank Statement
- Insurance EOB
- Research Paper
- Financial Report
- Unknown

Rules:
- "Bill" = utility bills, phone bills, cable bills, medical bills
- "Invoice" = commercial invoices from a vendor for goods/services
- "Receipt" = proof-of-purchase or payment confirmation
- "Research Paper" = academic papers, journal articles, conference papers, theses, preprints
- "Financial Report" = annual reports, earnings statements, 10-K/10-Q, quarterly reports
- "Insurance EOB" = Explanation of Benefits from health insurance
- "Bank Statement" = monthly bank or credit card account statements
- If unclear, respond "Unknown"

Document text:
---
{document_text}
---
"""


# ── Stage 3: Type-specific extraction prompts (text-only) ─────────────────────

FINANCIAL_EXTRACTION_PROMPT = """Below is the text content of a financial document (type: {doc_type}).
Extract all relevant data and return a strictly formatted JSON object.

The JSON structure must be:
{{
  "documentType": "{doc_type}",
  "vendorName": "string",
  "vendorAddress": "string or null",
  "invoiceNumber": "string or null",
  "date": "YYYY-MM-DD",
  "dueDate": "YYYY-MM-DD or null",
  "totalAmount": number,
  "taxAmount": number or 0,
  "currency": "USD",
  "accountNumber": "string or null",
  "billingPeriod": "string or null",
  "lineItems": [
    {{
      "description": "string",
      "quantity": number,
      "unitPrice": number,
      "total": number,
      "sku": "string or null"
    }}
  ],
  "summary": "1-sentence summary of this document"
}}

Rules:
1. Numerical values must be numbers, not strings.
2. Missing fields should be null (or 0 for numbers).
3. Dates as YYYY-MM-DD.
4. Output ONLY valid JSON. No markdown, no commentary, no thinking.

Document text:
---
{document_text}
---
"""

RESEARCH_PAPER_EXTRACTION_PROMPT = """Below is the text content of an academic research paper.
Extract all relevant metadata and return a strictly formatted JSON object.

The JSON structure must be:
{{
  "documentType": "Research Paper",
  "title": "string - full title of the paper",
  "authors": ["author1", "author2"],
  "abstract": "string - the full abstract text",
  "journal": "string - journal or conference name, or null",
  "doi": "string - DOI if visible, or null",
  "date": "YYYY-MM-DD or null",
  "publicationDate": "YYYY-MM-DD or null",
  "keywords": ["keyword1", "keyword2"],
  "methodology": "string - brief description of methodology, or null",
  "findings": "string - key findings or conclusions",
  "summary": "1-sentence summary of the paper"
}}

Rules:
1. Extract the FULL abstract if present.
2. List ALL authors visible.
3. Missing fields should be null.
4. Output ONLY valid JSON. No markdown, no commentary, no thinking.

Document text:
---
{document_text}
---
"""

FINANCIAL_REPORT_EXTRACTION_PROMPT = """Below is the text content of a financial report.
Extract all relevant data and return a strictly formatted JSON object.

The JSON structure must be:
{{
  "documentType": "Financial Report",
  "companyName": "string",
  "reportType": "string (e.g. Annual Report, 10-K, Quarterly, Earnings)",
  "reportPeriod": "string (e.g. FY 2024, Q3 2025)",
  "date": "YYYY-MM-DD or null",
  "revenue": number or null,
  "expenses": number or null,
  "netIncome": number or null,
  "currency": "USD",
  "keyMetrics": {{
    "metric_name": value
  }},
  "lineItems": [
    {{
      "description": "string - line item or category",
      "quantity": 0,
      "unitPrice": 0,
      "total": number
    }}
  ],
  "summary": "1-sentence summary of the report"
}}

Rules:
1. Numerical values must be numbers, not strings.
2. Express large numbers in full (e.g., 1500000 not 1.5M).
3. Missing fields should be null.
4. Output ONLY valid JSON. No markdown, no commentary, no thinking.

Document text:
---
{document_text}
---
"""


# Map document types → extraction prompts
_EXTRACTION_PROMPTS: Dict[DocumentType, str] = {
    DocumentType.INVOICE: FINANCIAL_EXTRACTION_PROMPT,
    DocumentType.RECEIPT: FINANCIAL_EXTRACTION_PROMPT,
    DocumentType.BILL: FINANCIAL_EXTRACTION_PROMPT,
    DocumentType.BANK_STATEMENT: FINANCIAL_EXTRACTION_PROMPT,
    DocumentType.INSURANCE_EOB: FINANCIAL_EXTRACTION_PROMPT,
    DocumentType.RESEARCH_PAPER: RESEARCH_PAPER_EXTRACTION_PROMPT,
    DocumentType.FINANCIAL_REPORT: FINANCIAL_REPORT_EXTRACTION_PROMPT,
    DocumentType.UNKNOWN: FINANCIAL_EXTRACTION_PROMPT,
}


# ── Confidence scoring ────────────────────────────────────────────────────────

def calculate_confidence(extracted_data: Dict[str, Any], doc_type: DocumentType) -> float:
    """Calculate confidence score based on document type and required fields"""
    if doc_type == DocumentType.RESEARCH_PAPER:
        required = ["title", "authors", "abstract"]
    elif doc_type == DocumentType.FINANCIAL_REPORT:
        required = ["companyName", "reportType", "reportPeriod"]
    else:
        required = ["vendorName", "totalAmount", "date"]

    present = sum(1 for f in required if extracted_data.get(f))
    base_score = present / len(required) if required else 0.5

    if extracted_data.get("lineItems"):
        base_score += 0.1
    if extracted_data.get("summary"):
        base_score += 0.05

    return min(round(base_score, 2), 1.0)


# ── JSON parsing ──────────────────────────────────────────────────────────────

def parse_json_response(text: str) -> Dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks and thinking tags"""
    # Strip <think>...</think> blocks (Qwen3 reasoning)
    import re
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Remove markdown code blocks
    if "```" in text:
        text = text.replace("```json", "").replace("```", "")

    # Find JSON object bounds
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1:
        text = text[first_brace:last_brace + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nRaw text: {text[:500]}")


# ── Stage 1: OCR with DeepSeek OCR2 (vision model) ───────────────────────────

async def ocr_document(images: List[str]) -> str:
    """Convert document images to clean markdown using DeepSeek OCR2"""
    try:
        response = ollama.chat(
            model=OCR_MODEL,
            messages=[{
                "role": "user",
                "content": OCR_PROMPT,
                "images": images[:3]  # Process up to 3 pages
            }]
        )
        return response["message"]["content"].strip()
    except Exception as e:
        if "model" in str(e).lower() or "not found" in str(e).lower():
            raise ValueError(
                f"Ollama model '{OCR_MODEL}' not found. "
                f"Please run: ollama pull {OCR_MODEL}"
            )
        raise ValueError(f"OCR failed: {e}")


# ── Stage 2: Classify with Qwen3 (text-only model) ───────────────────────────

async def classify_document(document_text: str) -> DocumentType:
    """Classify document type from its text content using Qwen3"""
    try:
        # Use first ~3000 chars for classification (enough to identify type)
        text_snippet = document_text[:3000]

        response = ollama.chat(
            model=REASONING_MODEL,
            messages=[{
                "role": "user",
                "content": CLASSIFICATION_PROMPT.format(document_text=text_snippet)
            }]
        )

        raw = response["message"]["content"].strip()

        # Strip <think> blocks if present
        import re
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        # Match to enum
        for dt in DocumentType:
            if dt.value.lower() in raw.lower():
                return dt

        return DocumentType.UNKNOWN
    except Exception as e:
        if "model" in str(e).lower() or "not found" in str(e).lower():
            raise ValueError(
                f"Ollama model '{REASONING_MODEL}' not found. "
                f"Please run: ollama pull {REASONING_MODEL}"
            )
        raise ValueError(f"Classification failed: {e}")


# ── Stage 3: Extract with Qwen3 (text-only model) ────────────────────────────

async def extract_with_type(document_text: str, doc_type: DocumentType) -> Dict[str, Any]:
    """Extract structured data using a type-specific prompt and Qwen3"""
    prompt_template = _EXTRACTION_PROMPTS.get(
        doc_type, _EXTRACTION_PROMPTS[DocumentType.UNKNOWN]
    )

    prompt = prompt_template.format(
        doc_type=doc_type.value,
        document_text=document_text
    )

    try:
        response = ollama.chat(
            model=REASONING_MODEL,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        text = response["message"]["content"]
        extracted = parse_json_response(text)

        # Ensure documentType is set correctly
        extracted["documentType"] = doc_type.value

        confidence = calculate_confidence(extracted, doc_type)

        return {
            "data": extracted,
            "confidence": confidence,
            "provider": f"ollama/{OCR_MODEL}+{REASONING_MODEL}",
            "classified_as": doc_type.value,
        }
    except Exception as e:
        if "model" in str(e).lower() or "not found" in str(e).lower():
            raise ValueError(
                f"Ollama model '{REASONING_MODEL}' not found. "
                f"Please run: ollama pull {REASONING_MODEL}"
            )
        raise ValueError(f"Extraction failed: {e}")


# ── Orchestrator ──────────────────────────────────────────────────────────────

async def extract_document(
    file_bytes: bytes,
    filename: str
) -> Dict[str, Any]:
    """
    Three-stage extraction pipeline:
      1. DeepSeek OCR2: image → clean markdown
      2. Qwen3: markdown → document type classification
      3. Qwen3: markdown + type-specific prompt → structured JSON

    Args:
        file_bytes: Raw file bytes
        filename: Original filename

    Returns:
        Dict with extracted data, confidence, provider, and classified_as
    """
    from .pdf_parser import parse_document

    # Parse document to get images for the OCR model
    parsed = parse_document(file_bytes, filename, strategy="vision")

    if not parsed.get("images"):
        raise ValueError("No images extracted from document")

    images = parsed["images"]

    # Stage 1: OCR — images → clean markdown text
    document_text = await ocr_document(images)

    if not document_text.strip():
        raise ValueError("OCR produced no text output")

    # Stage 2: Classify — markdown → document type
    doc_type = await classify_document(document_text)

    # Stage 3: Extract — markdown + type prompt → structured JSON
    return await extract_with_type(document_text, doc_type)

---
category:
- '[[App Development]]'
- '[[Coding with AI]]'
tags:
- personal
- projects
created: '2026-01-28'
updated: '2026-01-28'
---
# EOB Medical Expense Tracker - Product Requirements Document

## Overview
A lightweight Python macOS app that uses **vision LLM** to extract claim data from Anthem Blue Cross EOB PDFs and tracks medical expenses at the claim level.

## Problem Statement
Managing medical expenses requires manually reviewing Explanation of Benefits (EOB) documents to track:
- What was billed vs. what insurance paid
- Copays, deductibles, and coinsurance owed
- Progress toward annual deductible and out-of-pocket maximums

Current EOB PDFs from Anthem Blue Cross are difficult to parse programmatically due to:
- Mixed layouts (landscape tables on page 2, portrait on page 3+)
- Colored backgrounds that break traditional PDF table detection
- Non-standard table borders and styled boxes
- Text positioning that isn't grid-aligned

## Solution
Use vision-capable LLMs to "read" EOB documents like a human would, extracting structured JSON data that can be stored and analyzed.

### Extraction Pipeline
```
PDF Directory → pdf2image → Vision LLM → JSON → Validation → DuckDB
```

## Target User
Personal use - single user tracking their own family's medical expenses.

## Core Features

### 1. PDF Import & Extraction
- Import EOB PDFs from a folder
- Convert pages to images
- Extract structured data via local vision LLM (DeepSeek-OCR)
- Validate extracted data against Pydantic schemas
- Store in DuckDB with deduplication

### 2. Claims Tracking
- View all claims in a sortable/filterable table
- Click through to see line item details per claim
- Track by: date, provider, service type, amounts

### 3. Accumulator Tracking
- Monitor deductible progress (individual + family)
- Monitor out-of-pocket maximum progress
- Track both in-network and out-of-network separately
- Point-in-time snapshots from each EOB

### 4. Analytics Dashboard
- YTD spending summary
- Spending by provider
- Spending by month
- Accumulator progress bars

## Data Model

### Entities
| Table | Description |
|-------|-------------|
| members | People covered under the plan |
| documents | EOB PDFs (one row per file) |
| claims | Claims grouped by claim number |
| line_items | Individual services within a claim |
| accumulators | Point-in-time deductible/OOP snapshots |

### Key Fields Extracted
**From Page 1 (Summary):**
- Statement date
- Member name, ID
- Total billed, discounts, insurance paid, you pay

**From Page 2 (YTD Summary):**
- Deductible limits and applied amounts (individual/family, in/out of network)
- Out-of-pocket max limits and applied amounts

**From Page 3+ (Claims Details):**
- Claim number
- Provider name
- Service date, received date
- Per-line: service description, reason code, billed, allowed, copay, deductible, coinsurance, you pay

## Technical Requirements

### Vision LLM (Local)
| Model | Size | Ollama Command | Notes |
|-------|------|----------------|-------|
| DeepSeek-OCR | 3B (6.7GB) | `deepseek-ocr` | Primary - purpose-built for document OCR |
| olmOCR-2 | 7B (8.85GB) | `richardyoung/olmocr2:7b-q8` | Fallback - better on complex tables |

### Database
- **DuckDB** - columnar storage optimized for analytical queries
- Single file, embeddable, no server required

### GUI Framework
- **customtkinter** - modern-looking tkinter widgets for macOS

### Dependencies
```
pdf2image>=1.16.0     # PDF → PNG (requires poppler)
Pillow>=10.0.0        # Image handling
ollama>=0.4.0         # Local LLM client
pydantic>=2.0.0       # JSON validation
duckdb>=1.0.0         # Analytical database
customtkinter>=5.2.0  # Modern GUI
pandas>=2.0.0         # Data manipulation
matplotlib>=3.7.0     # Charts
```

### System Requirements
- macOS with Homebrew
- `brew install poppler` (for pdf2image)
- Ollama v0.13.0+ for local vision models
- ~7GB disk space for DeepSeek-OCR model

## Project Structure
```
eob_tracker/
├── main.py                  # App entry point
├── extractor/
│   ├── pdf_to_images.py     # PDF → PNG conversion
│   ├── vision_extract.py    # Ollama extraction
│   └── prompts.py           # Page-specific prompts
├── models/
│   └── schemas.py           # Pydantic models
├── database/
│   └── db.py                # DuckDB operations
├── gui/
│   ├── app.py               # Main window
│   ├── claims_view.py       # Claims table
│   └── dashboard.py         # Analytics view
└── data/
    └── eob.duckdb           # Database file
```

## Privacy
- All processing runs locally via Ollama
- No data leaves the machine
- No cloud APIs required (Claude API is optional fallback only)

## Out of Scope (Future)
- Export to CSV/Excel
- Manual correction UI for extraction errors
- Receipt/bill attachment linking
- Support for other insurance providers
- Multi-user support

## Success Criteria
1. Successfully extract data from all 47 existing EOB PDFs
2. No duplicate claims when re-importing same PDF
3. Dashboard totals match sum of individual line items
4. Deductible/OOP progress matches latest EOB snapshot

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
# EOB Tracker - Implementation Tasks

## Phase 0: Test Extraction Quality
*Validate vision LLM accuracy before building the pipeline*

- [ ] **0.1** Install poppler via Homebrew (`brew install poppler`)
- [ ] **0.2** Install/update Ollama to v0.13.0+
- [ ] **0.3** Pull DeepSeek-OCR model (`ollama pull deepseek-ocr`)
- [ ] **0.4** Convert sample EOB PDF to PNG images (one per page)
- [ ] **0.5** Test extraction on page 1 (claims summary)
  - Expected: statement_date, member_name, member_id, total_billed, total_discount, total_allowed, total_insurance_paid, total_you_pay
- [ ] **0.6** Test extraction on page 2 (YTD accumulators - landscape)
  - Expected: deductible/OOP limits and applied amounts for individual/family, in/out network
- [ ] **0.7** Test extraction on page 3 (claim details table)
  - Expected: claim_number, provider, service_date, received_date, line items with all cost breakdowns
- [ ] **0.8** Evaluate extraction quality
  - If accuracy < 90%, test olmOCR-2 fallback model
  - If local models insufficient, plan for Claude API integration

---

## Phase 1: Project Setup & Extraction Pipeline

### 1.1 Project Structure
- [ ] **1.1.1** Create `eob_tracker/` directory structure
- [ ] **1.1.2** Create `requirements.txt` with all dependencies
- [ ] **1.1.3** Set up Python virtual environment
- [ ] **1.1.4** Install all dependencies

### 1.2 Pydantic Schemas (`models/schemas.py`)
- [ ] **1.2.1** Define `Member` model
- [ ] **1.2.2** Define `Document` model (EOB metadata)
- [ ] **1.2.3** Define `Claim` model (claim-level aggregates)
- [ ] **1.2.4** Define `LineItem` model (per-service details)
- [ ] **1.2.5** Define `Accumulator` model (deductible/OOP snapshots)
- [ ] **1.2.6** Define extraction response models for each page type

### 1.3 PDF Conversion (`extractor/pdf_to_images.py`)
- [ ] **1.3.1** Implement `pdf_to_images(pdf_path) -> List[Path]`
- [ ] **1.3.2** Handle multi-page PDFs
- [ ] **1.3.3** Configure DPI for optimal OCR (suggest 200-300)
- [ ] **1.3.4** Add temp file cleanup

### 1.4 Extraction Prompts (`extractor/prompts.py`)
- [ ] **1.4.1** Create prompt for page 1 (summary extraction)
- [ ] **1.4.2** Create prompt for page 2 (accumulator extraction)
- [ ] **1.4.3** Create prompt for pages 3+ (claims/line items extraction)
- [ ] **1.4.4** Add JSON schema examples in prompts for better accuracy

### 1.5 Vision Extraction (`extractor/vision_extract.py`)
- [ ] **1.5.1** Implement Ollama client integration
- [ ] **1.5.2** Create `extract_page(image_path, page_type) -> dict`
- [ ] **1.5.3** Add retry logic for failed extractions
- [ ] **1.5.4** Validate responses against Pydantic schemas
- [ ] **1.5.5** Create `extract_eob(pdf_path) -> ExtractedEOB` orchestrator

---

## Phase 2: Database Layer

### 2.1 Schema Setup (`database/db.py`)
- [ ] **2.1.1** Create DuckDB connection manager
- [ ] **2.1.2** Implement `init_schema()` to create all 5 tables
- [ ] **2.1.3** Add indexes on frequently queried columns

### 2.2 CRUD Operations
- [ ] **2.2.1** Implement `upsert_member()`
- [ ] **2.2.2** Implement `upsert_document()`
- [ ] **2.2.3** Implement `upsert_claim()`
- [ ] **2.2.4** Implement `upsert_line_items()`
- [ ] **2.2.5** Implement `upsert_accumulators()`
- [ ] **2.2.6** Add deduplication logic by `claim_id`

### 2.3 Query Functions
- [ ] **2.3.1** `get_all_claims(filters)` - for claims table view
- [ ] **2.3.2** `get_line_items(claim_id)` - for detail view
- [ ] **2.3.3** `get_latest_accumulators()` - for dashboard
- [ ] **2.3.4** `get_spending_summary()` - aggregates for analytics

### 2.4 Import Pipeline
- [ ] **2.4.1** Create `import_eob(pdf_path)` - full extraction + save
- [ ] **2.4.2** Create `import_folder(folder_path)` - batch import
- [ ] **2.4.3** Add progress tracking for batch imports
- [ ] **2.4.4** Handle extraction errors gracefully (log and continue)

### 2.5 Testing
- [ ] **2.5.1** Import one EOB, manually verify all values match PDF
- [ ] **2.5.2** Re-import same EOB, verify no duplicates created
- [ ] **2.5.3** Verify line item totals sum to claim totals

---

## Phase 3: GUI - Core Views

### 3.1 Main Window (`gui/app.py`)
- [ ] **3.1.1** Set up customtkinter main window
- [ ] **3.1.2** Create sidebar navigation (Import, Claims, Dashboard)
- [ ] **3.1.3** Implement view switching

### 3.2 Claims View (`gui/claims_view.py`)
- [ ] **3.2.1** Create claims table with columns: Date, Provider, Billed, You Pay, Status
- [ ] **3.2.2** Add sorting by clicking column headers
- [ ] **3.2.3** Add filtering by date range
- [ ] **3.2.4** Add filtering by provider (dropdown)
- [ ] **3.2.5** Implement row click → line items detail popup

### 3.3 Import View
- [ ] **3.3.1** Add "Select Folder" button with file dialog
- [ ] **3.3.2** Show list of PDFs found in folder
- [ ] **3.3.3** Add "Preview" button to test extraction on one file
- [ ] **3.3.4** Show extraction preview in a scrollable panel
- [ ] **3.3.5** Add "Import All" button with progress bar
- [ ] **3.3.6** Show success/error summary after import

---

## Phase 4: GUI - Dashboard & Analytics

### 4.1 Dashboard View (`gui/dashboard.py`)
- [ ] **4.1.1** YTD spending summary cards (Billed, Discounts, Insurance Paid, You Paid)
- [ ] **4.1.2** Deductible progress bar (individual in-network)
- [ ] **4.1.3** OOP max progress bar (individual in-network)
- [ ] **4.1.4** Family-level progress bars

### 4.2 Charts
- [ ] **4.2.1** Spending by month (bar chart)
- [ ] **4.2.2** Spending by provider (pie or bar chart)
- [ ] **4.2.3** Claims count over time

---

## Phase 5: Final Testing & Polish

- [ ] **5.1** Import all 47 EOB PDFs
- [ ] **5.2** Verify no duplicate claims
- [ ] **5.3** Verify dashboard totals match sum of claims
- [ ] **5.4** Test on "Unknown" named PDFs for edge cases
- [ ] **5.5** Add error handling for corrupt/unreadable PDFs
- [ ] **5.6** Polish UI spacing and alignment
- [ ] **5.7** Write brief README with setup instructions

---

## Optional / Future Enhancements

- [ ] Export claims to CSV
- [ ] Manual edit UI for extraction corrections
- [ ] Link receipts/bills to claims
- [ ] Support additional insurance providers
- [ ] Dark mode support

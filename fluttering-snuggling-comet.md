# DocuExtract AI - Architecture Consultation

## Current State Summary
- **Stack**: React 19 + TypeScript + Vite frontend
- **AI**: Google Gemini API (gemini-2.5-flash-image)
- **Purpose**: Financial document extraction (invoices, receipts, statements, EOBs)
- **Stage**: Functional MVP with batch processing and CSV export

---

## 1. System Design: Document Extraction Pipeline Architecture

### Current Architecture (Monolithic Frontend)
```
┌─────────────────────────────────────────────────────┐
│                    Browser                          │
│  ┌─────────┐   ┌──────────┐   ┌─────────────────┐  │
│  │ Upload  │ → │ Base64   │ → │ Gemini API Call │  │
│  │  UI     │   │ Convert  │   │   (Direct)      │  │
│  └─────────┘   └──────────┘   └─────────────────┘  │
│                                       ↓            │
│                              ┌─────────────────┐   │
│                              │  Results Table  │   │
│                              │  + CSV Export   │   │
│                              └─────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Recommended Architecture (Production-Ready)
```
┌─────────────┐     ┌─────────────────────────────────────────────┐
│   Client    │     │              Backend Services               │
│  (React)    │     │                                             │
├─────────────┤     │  ┌─────────┐   ┌──────────┐   ┌──────────┐ │
│             │ API │  │ Upload  │   │  Queue   │   │ Extract  │ │
│  Upload UI  │────→│  │ Service │ → │ (Redis/  │ → │ Workers  │ │
│             │     │  │         │   │  BullMQ) │   │          │ │
├─────────────┤     │  └─────────┘   └──────────┘   └──────────┘ │
│             │     │       ↓                            ↓       │
│  Results    │←────│  ┌─────────┐   ┌──────────┐   ┌──────────┐ │
│  Dashboard  │ WS  │  │   S3/   │   │ Postgres │   │  LLM     │ │
│             │     │  │  Minio  │   │   + ORM  │   │ Gateway  │ │
└─────────────┘     │  └─────────┘   └──────────┘   └──────────┘ │
                    └─────────────────────────────────────────────┘
```

### Key Architectural Components

| Component | Purpose | Technology Options |
|-----------|---------|-------------------|
| **API Gateway** | Auth, rate limiting, routing | FastAPI / Express / Kong |
| **Upload Service** | File validation, virus scan, storage | Presigned URLs + S3/Minio |
| **Job Queue** | Async processing, retry, prioritization | BullMQ (Node) / Celery (Python) / RQ |
| **Extract Workers** | Document processing, LLM calls | Horizontal scaling, stateless |
| **LLM Gateway** | Provider abstraction, fallback, caching | LiteLLM / custom router |
| **Results Store** | Structured data, search, export | PostgreSQL + pgvector |
| **Object Storage** | Original docs + processed outputs | S3 / Minio / Cloudflare R2 |

### Data Flow Recommendations

1. **Upload Phase**
   - Generate presigned URL for direct-to-storage upload
   - Validate file type, size, and run virus scan
   - Create job record with `pending` status

2. **Processing Phase**
   - Worker claims job from queue
   - Fetch document from storage
   - Pre-process (convert PDF to images if needed)
   - Send to LLM with structured output schema
   - Parse and validate response

3. **Storage Phase**
   - Store structured extraction in Postgres
   - Store raw LLM response for audit
   - Update job status, notify client via WebSocket

---

## 2. Technology Choices: OCR vs LLM-Based Extraction

### Comparison Matrix

| Criteria | Traditional OCR | LLM Vision | Hybrid Approach |
|----------|-----------------|------------|-----------------|
| **Accuracy (clean docs)** | 95-99% | 90-98% | 98-99% |
| **Accuracy (messy docs)** | 60-80% | 85-95% | 90-98% |
| **Speed** | Fast (100ms) | Slow (2-5s) | Medium (1-3s) |
| **Cost per doc** | $0.001-0.01 | $0.01-0.10 | $0.01-0.05 |
| **Structured extraction** | Requires templates | Natural | Best of both |
| **New doc types** | Template creation | Zero-shot | Minimal config |
| **Privacy** | Local possible | API = cloud | Depends on LLM |

### Recommendation: Tiered Hybrid Approach

```
Document Input
      ↓
┌─────────────────┐
│ Document Triage │ ← Quick classification (local, fast)
└────────┬────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
┌───────┐ ┌────────┐
│ Known │ │ Novel  │
│ Type  │ │ Type   │
└───┬───┘ └───┬────┘
    ↓         ↓
┌───────┐ ┌────────┐
│ OCR + │ │ LLM    │
│Template│ │ Vision │
└───┬───┘ └───┬────┘
    ↓         ↓
┌─────────────────┐
│ Validation &    │
│ Confidence Score│
└────────┬────────┘
         ↓
   Low Confidence?
    ↓         ↓
   Yes        No
    ↓         ↓
┌───────┐ ┌────────┐
│ Human │ │ Store  │
│ Review│ │ Result │
└───────┘ └────────┘
```

### Technology Stack Options

**For OCR Layer:**
| Tool | Type | Best For |
|------|------|----------|
| Tesseract 5 | Open source | Budget, local processing |
| Google Document AI | Cloud API | High accuracy, structured forms |
| AWS Textract | Cloud API | AWS ecosystem, tables/forms |
| Azure Form Recognizer | Cloud API | Pre-built models, custom training |
| PaddleOCR | Open source | Best OSS accuracy, multilingual |

**For LLM Layer:**
| Provider | Model | Cost/1K tokens | Speed |
|----------|-------|----------------|-------|
| Google | Gemini 2.5 Flash | $0.075 input | Fast |
| OpenAI | GPT-4o | $2.50 input | Medium |
| Anthropic | Claude 3.5 Sonnet | $3.00 input | Medium |
| Local | Qwen2-VL / LLaVA | Infrastructure | Variable |

**Current Recommendation** (for your financial doc use case):
- **Primary**: Stick with Gemini 2.5 Flash (good price/performance)
- **Add**: Local OCR pre-pass with Tesseract or PaddleOCR
- **Future**: Self-hosted Qwen2-VL for privacy-sensitive clients

---

## 3. Scalability: High-Volume Document Processing

### Current Limitations
- Max 2 concurrent requests (frontend-limited)
- No persistent job queue
- Single API provider (no failover)
- No caching (duplicate docs re-processed)
- Results stored only in browser memory

### Scalability Tiers

#### Tier 1: Small Scale (< 1,000 docs/day)
**Current architecture is sufficient with minor enhancements:**
- Add document hash deduplication
- Implement browser-side result caching (IndexedDB)
- Add retry logic with exponential backoff
- Increase concurrent processing to 5

#### Tier 2: Medium Scale (1,000 - 50,000 docs/day)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Load        │     │ API         │     │ Worker Pool │
│ Balancer    │────→│ Servers x3  │────→│ x5-10       │
└─────────────┘     └─────────────┘     └─────────────┘
                           ↓                   ↓
                    ┌─────────────┐     ┌─────────────┐
                    │ Redis Queue │     │ PostgreSQL  │
                    │ + Pub/Sub   │     │ (Primary)   │
                    └─────────────┘     └─────────────┘
```

**Requirements:**
- Backend API layer (FastAPI/Express)
- Redis for job queue (BullMQ or Celery)
- PostgreSQL for results storage
- S3-compatible storage for documents
- Docker + Docker Compose orchestration
- Horizontal worker scaling

#### Tier 3: Large Scale (50,000+ docs/day)
```
┌────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                     │
├────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ Ingress  │ │ API      │ │ Workers  │ │ Workers  │       │
│ │ + CDN    │ │ Pods x5  │ │ Pool A   │ │ Pool B   │       │
│ └──────────┘ └──────────┘ │ (Gemini) │ │ (Local)  │       │
│                           └──────────┘ └──────────┘       │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ Redis    │ │ Postgres │ │ S3/Minio │ │ Monitoring│      │
│ │ Cluster  │ │ HA       │ │ HA       │ │ Stack    │       │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└────────────────────────────────────────────────────────────┘
```

**Additional Requirements:**
- Kubernetes for orchestration
- Auto-scaling based on queue depth
- Multiple LLM provider failover
- Read replicas for PostgreSQL
- CDN for static assets
- Distributed tracing (Jaeger/Tempo)
- Metrics (Prometheus + Grafana)

### Specific Scaling Strategies

#### 1. Document Deduplication
```typescript
// Hash-based deduplication
const docHash = await crypto.subtle.digest('SHA-256', fileBuffer);
const existing = await db.query(
  'SELECT id, results FROM extractions WHERE doc_hash = $1',
  [docHash]
);
if (existing) return existing.results; // Skip processing
```

#### 2. Batch API Calls
```typescript
// Batch multiple small documents in single API call
const batchPrompt = documents.map((doc, i) =>
  `Document ${i + 1}:\n${doc.content}`
).join('\n---\n');
const results = await llm.extract(batchPrompt);
```

#### 3. Priority Queues
```typescript
// Separate queues by document type/urgency
const queues = {
  high: new Queue('extract:high'),    // Urgent single docs
  normal: new Queue('extract:normal'), // Standard processing
  batch: new Queue('extract:batch'),   // Large batch jobs
};
```

#### 4. Result Caching
```typescript
// Cache extraction results by document hash + prompt version
const cacheKey = `extract:${docHash}:${promptVersion}`;
const cached = await redis.get(cacheKey);
if (cached) return JSON.parse(cached);
```

---

## Architecture Decision Records (ADRs)

### ADR-001: API vs Browser-Direct LLM Calls
**Decision**: Migrate to backend API layer
**Rationale**:
- API key security (not exposed in browser)
- Better rate limiting and retry handling
- Enables job queue for reliability
- Required for multi-user support

### ADR-002: LLM Provider Strategy
**Decision**: LiteLLM gateway with multi-provider support
**Rationale**:
- Single interface to multiple providers
- Automatic failover on errors
- Cost optimization routing
- Easy to add/remove providers

### ADR-003: Storage Strategy
**Decision**: S3-compatible object storage + PostgreSQL
**Rationale**:
- Object storage for documents (versioning, lifecycle)
- PostgreSQL for structured extractions (queries, export)
- Separate concerns, independent scaling

---

## Implementation Roadmap

### Phase 1: Backend Foundation (2-3 weeks)
- [ ] FastAPI backend with upload endpoint
- [ ] PostgreSQL schema for jobs and results
- [ ] Redis queue with BullMQ or RQ
- [ ] Single worker process
- [ ] Docker Compose setup

### Phase 2: Production Hardening (2 weeks)
- [ ] Authentication (API keys or OAuth)
- [ ] Rate limiting per user
- [ ] Document validation and virus scan
- [ ] Error handling and retry logic
- [ ] Monitoring and alerting

### Phase 3: Scale Optimization (2 weeks)
- [ ] LiteLLM gateway integration
- [ ] Document deduplication
- [ ] Result caching layer
- [ ] WebSocket status updates
- [ ] Batch export (ZIP, JSON)

### Phase 4: Enterprise Features (ongoing)
- [ ] Multi-tenant support
- [ ] Custom extraction templates
- [ ] Human-in-the-loop review UI
- [ ] Audit logging
- [ ] Self-hosted LLM option

---

## TAILORED RECOMMENDATIONS

Based on your requirements:
- **Volume**: < 100 docs/day
- **Privacy**: Prefer local processing
- **Cost**: Free/minimal

### Revised Architecture: Local-First MVP

```
┌─────────────────────────────────────────────────────┐
│                    Your Machine                      │
│  ┌─────────┐   ┌──────────┐   ┌─────────────────┐  │
│  │ React   │ → │ Local    │ → │ Ollama          │  │
│  │  UI     │   │ FastAPI  │   │ (Qwen2-VL)      │  │
│  └─────────┘   └──────────┘   └─────────────────┘  │
│                      ↓              ↓               │
│               ┌──────────┐   ┌─────────────────┐   │
│               │ DuckDB   │   │ Gemini Fallback │   │
│               │ (Results)│   │ (Complex docs)  │   │
│               └──────────┘   └─────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Recommended Tech Stack (Free/Local)

| Component | Technology | Cost |
|-----------|-----------|------|
| **LLM (Primary)** | Ollama + Qwen2-VL-7B | Free (local) |
| **LLM (Fallback)** | Gemini Flash (free tier) | Free (limited) |
| **PDF Parsing** | PyMuPDF + pdfplumber | Free |
| **OCR Boost** | Tesseract 5 or PaddleOCR | Free |
| **Backend** | FastAPI (Python) | Free |
| **Database** | DuckDB | Free |
| **Storage** | Local filesystem | Free |

### Environment Setup with uv

**uv** is a fast Python package manager and virtual environment tool. Use it for all Python dependency management.

#### Initial Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install all dependencies
cd /Users/richardyu/PARA/1_projects/docuextract-ai
uv venv
source .venv/bin/activate  # or .venv/Scripts/activate on Windows

# Install all required packages
uv pip install \
    fastapi \
    uvicorn \
    duckdb \
    pymupdf \
    pdfplumber \
    pdf2image \
    ollama \
    google-generativeai \
    python-multipart \
    aiofiles

# Generate requirements.txt for reproducibility
uv pip freeze > requirements.txt
```

#### Project Structure
```
docuextract-ai/
├── .venv/                    # Virtual environment (managed by uv)
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Frozen dependencies
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── extraction.py        # LLM extraction logic
│   ├── pdf_parser.py        # PDF parsing utilities
│   └── database.py          # DuckDB operations
├── frontend/                # Existing React app
│   ├── App.tsx
│   └── ...
└── extractions.duckdb       # Local database
```

#### pyproject.toml
```toml
[project]
name = "docuextract-ai"
version = "0.1.0"
description = "Local-first document extraction with vision LLMs"
requires-python = ">=3.11"

[project.dependencies]
fastapi = ">=0.115.0"
uvicorn = ">=0.34.0"
duckdb = ">=1.1.0"
pymupdf = ">=1.25.0"
pdfplumber = ">=0.11.0"
pdf2image = ">=1.17.0"
ollama = ">=0.4.0"
google-generativeai = ">=0.8.0"
python-multipart = ">=0.0.18"
aiofiles = ">=24.0.0"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "httpx>=0.28.0",
]
```

---

## Detailed Implementation Tasks

### Component 1: Environment Setup

- [ ] **1.1** Install uv package manager
  - `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Verify: `uv --version`

- [ ] **1.2** Create virtual environment
  - `cd /Users/richardyu/PARA/1_projects/docuextract-ai`
  - `uv venv`
  - `source .venv/bin/activate`

- [ ] **1.3** Create pyproject.toml with all dependencies
  - Project metadata
  - All production dependencies
  - Dev dependencies (pytest, httpx)

- [ ] **1.4** Install all Python packages
  - `uv pip install -e .` (install from pyproject.toml)
  - Verify: `python -c "import fastapi, duckdb, pymupdf; print('OK')"`

- [ ] **1.5** Install Poppler for pdf2image (required for PDF to image conversion)
  - macOS: `brew install poppler`
  - Verify: `pdftoppm -v`

---

### Component 2: Ollama LLM Setup

- [ ] **2.1** Install Ollama
  - macOS: `brew install ollama`
  - Linux: `curl -fsSL https://ollama.com/install.sh | sh`
  - Verify: `ollama --version`

- [ ] **2.2** Start Ollama server
  - `ollama serve` (runs on localhost:11434)
  - Verify: `curl http://localhost:11434/api/tags`

- [ ] **2.3** Pull Qwen2-VL model
  - `ollama pull qwen2-vl:7b` (~5GB download)
  - Verify: `ollama list` shows qwen2-vl:7b

- [ ] **2.4** Test vision model with sample image
  - Create test script with base64 image
  - Verify extraction output is valid JSON

- [ ] **2.5** (Optional) Pull backup model
  - `ollama pull llava:13b` (alternative if Qwen struggles)

---

### Component 3: PDF Parsing Module

- [ ] **3.1** Create `backend/pdf_parser.py`
  - Import PyMuPDF, pdfplumber, pdf2image

- [ ] **3.2** Implement `extract_text(pdf_bytes)` function
  - Use PyMuPDF for fast text extraction
  - Return list of page texts

- [ ] **3.3** Implement `extract_tables(pdf_bytes)` function
  - Use pdfplumber for table detection
  - Return list of tables as dicts

- [ ] **3.4** Implement `pdf_to_images(pdf_bytes)` function
  - Use pdf2image to convert pages
  - Return list of PIL Images
  - Support DPI parameter (default: 200)

- [ ] **3.5** Implement `parse_document(file_bytes, strategy)` router
  - Strategy: "text", "vision", "hybrid"
  - Auto-detect if PDF or image
  - Return preprocessed content for LLM

- [ ] **3.6** Add unit tests for PDF parsing
  - Test with sample invoice PDF
  - Test with sample receipt image
  - Test error handling for corrupt files

---

### Component 4: LLM Extraction Module

- [ ] **4.1** Create `backend/extraction.py`
  - Import ollama, google.generativeai

- [ ] **4.2** Implement `ollama_extract(images, prompt)` function
  - Send images to local Qwen2-VL
  - Parse JSON response
  - Return ExtractedData or raise error

- [ ] **4.3** Implement `gemini_extract(images, prompt)` function
  - Use existing prompt from geminiService.ts
  - Handle API rate limits
  - Return ExtractedData or raise error

- [ ] **4.4** Implement extraction router with fallback
  ```python
  async def extract_document(file_bytes):
      try:
          result = await ollama_extract(...)
          if result.confidence > 0.8:
              return result
      except:
          pass
      return await gemini_extract(...)
  ```

- [ ] **4.5** Create Pydantic models for extraction
  - ExtractedData model matching TypeScript types
  - LineItem model
  - DocumentType enum

- [ ] **4.6** Implement confidence scoring
  - Check for required fields (vendor, amount, date)
  - Validate amount parsing
  - Return 0-1 confidence score

- [ ] **4.7** Add extraction prompt template
  - Port prompt from existing geminiService.ts
  - Optimize for Qwen2-VL format

---

### Component 5: DuckDB Database

- [ ] **5.1** Create `backend/database.py`
  - Import duckdb

- [ ] **5.2** Implement `init_database()` function
  - Create extractions.duckdb file
  - Create tables schema

- [ ] **5.3** Design database schema
  ```sql
  CREATE TABLE extractions (
      id VARCHAR PRIMARY KEY,
      doc_hash VARCHAR UNIQUE,
      filename VARCHAR,
      document_type VARCHAR,
      vendor_name VARCHAR,
      total_amount DECIMAL(15,2),
      currency VARCHAR(3),
      date DATE,
      raw_json JSON,
      created_at TIMESTAMP DEFAULT now()
  );

  CREATE TABLE line_items (
      id VARCHAR PRIMARY KEY,
      extraction_id VARCHAR REFERENCES extractions(id),
      description VARCHAR,
      quantity DECIMAL(10,2),
      unit_price DECIMAL(15,2),
      total DECIMAL(15,2)
  );
  ```

- [ ] **5.4** Implement `save_extraction(result)` function
  - Generate document hash for deduplication
  - Insert extraction + line items
  - Return extraction ID

- [ ] **5.5** Implement `get_extraction(id)` function
  - Fetch extraction by ID
  - Include line items
  - Return as Pydantic model

- [ ] **5.6** Implement `list_extractions(filters)` function
  - Support filtering by date range, vendor, document type
  - Support pagination (offset, limit)
  - Return list with total count

- [ ] **5.7** Implement `check_duplicate(doc_hash)` function
  - Query by document hash
  - Return existing extraction if found

- [ ] **5.8** Implement export functions
  - `export_to_csv(extraction_ids)` → CSV bytes
  - `export_to_parquet(extraction_ids)` → Parquet bytes

---

### Component 6: FastAPI Backend

- [ ] **6.1** Create `backend/main.py`
  - Import FastAPI, CORS middleware

- [ ] **6.2** Configure CORS for frontend
  - Allow localhost:3000 (Vite dev server)
  - Allow localhost:5173 (alternate Vite port)

- [ ] **6.3** Implement `POST /api/extract` endpoint
  - Accept file upload (multipart/form-data)
  - Validate file type (PDF, PNG, JPG, etc.)
  - Validate file size (<10MB)
  - Call extraction pipeline
  - Return ExtractedData JSON

- [ ] **6.4** Implement `GET /api/extractions` endpoint
  - Support query params: date_from, date_to, vendor, type
  - Support pagination: offset, limit
  - Return paginated list

- [ ] **6.5** Implement `GET /api/extractions/{id}` endpoint
  - Return single extraction with line items

- [ ] **6.6** Implement `GET /api/extractions/export` endpoint
  - Accept format query param (csv, parquet)
  - Accept extraction_ids query param
  - Return file download

- [ ] **6.7** Implement `GET /api/health` endpoint
  - Check Ollama connection
  - Check DuckDB connection
  - Return status JSON

- [ ] **6.8** Add error handling middleware
  - Catch validation errors → 400
  - Catch extraction errors → 500
  - Log all errors

- [ ] **6.9** Create startup event
  - Initialize database
  - Check Ollama availability
  - Log startup status

---

### Component 7: Frontend Integration

- [ ] **7.1** Create `services/backendService.ts`
  - Replace direct Gemini calls
  - Implement `extractDocument(file)` → fetch to backend
  - Implement `listExtractions()` → fetch history
  - Implement `exportExtractions(ids, format)` → download

- [ ] **7.2** Update `App.tsx` to use backend service
  - Replace geminiService import
  - Update extraction flow to use new service
  - Handle backend errors

- [ ] **7.3** Update environment config
  - Add VITE_BACKEND_URL env variable
  - Default to http://localhost:8000

- [ ] **7.4** Add extraction history view
  - New component: `ExtractionHistory.tsx`
  - Table with past extractions
  - Click to view details
  - Filter by date/vendor

- [ ] **7.5** Update FileSidebar to show history
  - Add "History" tab
  - Show recent extractions from database

- [ ] **7.6** Test full integration
  - Upload document via UI
  - Verify extraction via backend
  - Verify storage in DuckDB
  - Verify history retrieval

---

### Component 8: Error Correction & Learning System

This feature allows users to highlight extraction errors, correct them, and have the system learn from corrections to improve future extractions.

#### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Correction Workflow                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────────┐    │
│  │ Extracted│   │ User Reviews │   │ Correction       │    │
│  │ Results  │ → │ & Highlights │ → │ Stored           │    │
│  │          │   │ Errors       │   │                  │    │
│  └──────────┘   └──────────────┘   └──────────────────┘    │
│                        ↓                    ↓               │
│               ┌──────────────┐   ┌──────────────────┐      │
│               │ Document     │   │ Correction       │      │
│               │ Annotation   │   │ Database         │      │
│               │ UI           │   │ (DuckDB)         │      │
│               └──────────────┘   └──────────────────┘      │
│                                          ↓                  │
│                                ┌──────────────────┐        │
│                                │ Learning Engine  │        │
│                                │ - Few-shot examples       │
│                                │ - Pattern matching        │
│                                │ - Prompt refinement       │
│                                └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

- [ ] **8.1** Design corrections database schema
  ```sql
  CREATE TABLE corrections (
      id VARCHAR PRIMARY KEY,
      extraction_id VARCHAR REFERENCES extractions(id),
      field_name VARCHAR,           -- e.g., 'vendor_name', 'total_amount'
      original_value VARCHAR,       -- What the LLM extracted
      corrected_value VARCHAR,      -- User's correction
      document_region JSON,         -- {x, y, width, height, page}
      screenshot_base64 TEXT,       -- Cropped region of document
      created_at TIMESTAMP DEFAULT now()
  );

  CREATE TABLE correction_patterns (
      id VARCHAR PRIMARY KEY,
      field_name VARCHAR,
      pattern_type VARCHAR,         -- 'vendor_alias', 'date_format', 'amount_format'
      pattern_key VARCHAR,          -- e.g., 'ACME CORP' for vendor alias
      pattern_value VARCHAR,        -- e.g., 'Acme Corporation'
      confidence DECIMAL(3,2),      -- Based on correction frequency
      created_at TIMESTAMP DEFAULT now()
  );
  ```

- [ ] **8.2** Create `CorrectionUI.tsx` component
  - Display extracted results alongside document preview
  - Click on field to highlight corresponding region on document
  - Allow editing any extracted field
  - Visual diff: original vs corrected values

- [ ] **8.3** Implement document annotation overlay
  - Canvas overlay on document preview
  - Draw bounding boxes around problematic regions
  - Color-coded: green (correct), yellow (corrected), red (missing)
  - Support PDF page navigation with annotations

- [ ] **8.4** Create `backend/corrections.py` module
  - `save_correction(extraction_id, field, original, corrected, region)`
  - `get_corrections(extraction_id)` → list of corrections
  - `get_correction_patterns(field_name)` → learned patterns

- [ ] **8.5** Implement correction API endpoints
  - `POST /api/extractions/{id}/corrections` - Submit field correction
  - `GET /api/extractions/{id}/corrections` - Get all corrections for extraction
  - `POST /api/extractions/{id}/retry` - Re-extract with corrections as context

- [ ] **8.6** Implement pattern learning engine
  ```python
  def learn_from_correction(correction: Correction):
      # Learn vendor aliases
      if correction.field_name == 'vendor_name':
          save_pattern(
              pattern_type='vendor_alias',
              pattern_key=correction.original_value.lower(),
              pattern_value=correction.corrected_value
          )

      # Learn date formats
      if correction.field_name == 'date':
          date_format = detect_date_format(correction.original_value)
          save_pattern(
              pattern_type='date_format',
              pattern_key=date_format,
              pattern_value=correction.corrected_value
          )
  ```

- [ ] **8.7** Implement pre-extraction pattern application
  ```python
  def apply_patterns(raw_extraction: dict) -> dict:
      """Apply learned patterns before returning results"""
      patterns = get_all_patterns()

      # Apply vendor aliases
      if raw_extraction['vendor_name']:
          vendor_key = raw_extraction['vendor_name'].lower()
          if vendor_key in patterns['vendor_alias']:
              raw_extraction['vendor_name'] = patterns['vendor_alias'][vendor_key]

      return raw_extraction
  ```

- [ ] **8.8** Implement retry with corrections context
  ```python
  async def retry_extraction(extraction_id: str) -> ExtractedData:
      # Get original document
      extraction = get_extraction(extraction_id)
      corrections = get_corrections(extraction_id)

      # Build correction context for prompt
      correction_context = "Previous extraction had these errors:\n"
      for c in corrections:
          correction_context += f"- {c.field_name}: '{c.original_value}' should be '{c.corrected_value}'\n"
          if c.document_region:
              correction_context += f"  (located at region: {c.document_region})\n"

      # Re-extract with context
      return await extract_document(
          extraction.document_bytes,
          additional_context=correction_context
      )
  ```

- [ ] **8.9** Implement few-shot learning from corrections
  ```python
  def build_few_shot_examples(doc_type: str, limit: int = 3) -> str:
      """Build few-shot examples from corrected extractions"""
      corrections = get_recent_corrections(doc_type, limit)

      examples = ""
      for corr in corrections:
          examples += f"""
  Example document region: {corr.screenshot_description}
  Incorrect extraction: {corr.original_value}
  Correct value: {corr.corrected_value}

  """
      return examples
  ```

- [ ] **8.10** Create `CorrectionHistory.tsx` component
  - List of past corrections
  - Filter by field type, date range
  - Show correction frequency per field
  - "Patterns learned" summary

- [ ] **8.11** Implement correction confidence scoring
  - Track correction frequency per pattern
  - Auto-apply high-confidence patterns (>90%)
  - Flag medium-confidence patterns for user review (50-90%)
  - Suggest low-confidence patterns (<50%)

- [ ] **8.12** Add correction analytics dashboard
  - Extraction accuracy over time
  - Most corrected fields
  - Most effective learned patterns
  - Vendor-specific accuracy rates

---

### Component 9: Testing & Verification

- [ ] **9.1** Create `tests/` directory structure
  - `tests/test_pdf_parser.py`
  - `tests/test_extraction.py`
  - `tests/test_database.py`
  - `tests/test_api.py`
  - `tests/test_corrections.py`

- [ ] **9.2** Add sample test documents
  - `tests/fixtures/sample_invoice.pdf`
  - `tests/fixtures/sample_receipt.jpg`
  - `tests/fixtures/sample_statement.pdf`

- [ ] **9.3** Write PDF parser tests
  - Test text extraction
  - Test table extraction
  - Test image conversion

- [ ] **9.4** Write extraction tests
  - Test Ollama extraction
  - Test Gemini fallback
  - Test confidence scoring

- [ ] **9.5** Write database tests
  - Test CRUD operations
  - Test deduplication
  - Test export functions

- [ ] **9.6** Write correction system tests
  - Test correction storage
  - Test pattern learning
  - Test retry with context
  - Test few-shot example generation

- [ ] **9.7** Write API integration tests
  - Test all endpoints
  - Test error handling
  - Test file validation
  - Test correction endpoints

- [ ] **9.8** Manual E2E test checklist
  - [ ] Start backend: `uvicorn backend.main:app --reload`
  - [ ] Start frontend: `npm run dev`
  - [ ] Upload PDF document
  - [ ] Verify extraction appears in results
  - [ ] Correct an extraction error
  - [ ] Verify correction is stored
  - [ ] Retry extraction with corrections
  - [ ] Upload similar document - verify pattern applied
  - [ ] Download CSV export
  - [ ] Check history view
  - [ ] Upload duplicate document (should be deduplicated)

---

## Quick Reference: Implementation Order

1. **Environment** (1.1-1.5) → Foundation
2. **Ollama** (2.1-2.5) → Local LLM ready
3. **Database** (5.1-5.8) → Storage ready
4. **PDF Parser** (3.1-3.6) → Input processing
5. **Extraction** (4.1-4.7) → Core logic
6. **API** (6.1-6.9) → Backend complete
7. **Frontend** (7.1-7.6) → Full integration
8. **Corrections** (8.1-8.12) → Learning system
9. **Testing** (9.1-9.8) → Verification

**Total: 65 tasks** across 9 components

### Local LLM Options Comparison

| Model | Size | VRAM Needed | Quality | Speed |
|-------|------|-------------|---------|-------|
| **Qwen2-VL-7B** | 5GB | 8GB | Excellent | Fast |
| **LLaVA-1.6-34B** | 20GB | 24GB+ | Best | Slow |
| **MiniCPM-V-2.6** | 3GB | 6GB | Good | Very Fast |
| **Phi-3-Vision** | 4GB | 6GB | Good | Fast |

**Recommendation**: Start with **Qwen2-VL-7B** - best balance of quality and speed for document extraction on consumer hardware.

### Gemini Free Tier Details
- 15 requests/minute, 1,500 requests/day
- At <100 docs/day, this is sufficient as fallback
- Use for complex multi-page documents local LLM struggles with

### Hybrid Strategy

```python
async def extract_document(file: bytes) -> ExtractedData:
    # Try local first (free, private)
    try:
        result = await ollama_extract(file)
        if result.confidence > 0.8:
            return result
    except Exception:
        pass

    # Fallback to Gemini (free tier)
    return await gemini_extract(file)
```

### PDF Parsing Libraries

For extracting text/images from PDFs before LLM processing, here are your options:

| Library | Approach | Best For | Install |
|---------|----------|----------|---------|
| **PyMuPDF (fitz)** | Native rendering | Fast text + image extraction | `pip install pymupdf` |
| **pdf2image + Poppler** | PDF to image conversion | Vision LLM input | `pip install pdf2image` |
| **pdfplumber** | Table-aware extraction | Structured tables, forms | `pip install pdfplumber` |
| **pypdf** | Pure Python | Simple text extraction | `pip install pypdf` |
| **Unstructured** | ML-powered parsing | Complex layouts, mixed content | `pip install unstructured` |
| **docling** | IBM's document parser | Enterprise docs, high accuracy | `pip install docling` |
| **marker-pdf** | ML layout detection | Academic papers, columns | `pip install marker-pdf` |

#### Recommended Combinations

**For Vision LLM (Qwen2-VL):**
```python
# Convert PDF pages to images for vision model
from pdf2image import convert_from_bytes

def pdf_to_images(pdf_bytes: bytes) -> list[Image]:
    return convert_from_bytes(pdf_bytes, dpi=200)
```

**For Text Extraction + Tables:**
```python
# pdfplumber for table-heavy documents
import pdfplumber

def extract_tables(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        tables = []
        for page in pdf.pages:
            tables.extend(page.extract_tables())
    return tables
```

**For Complex Layouts (Hybrid):**
```python
# docling for complex enterprise documents
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(pdf_path)
markdown = result.document.export_to_markdown()
```

#### Performance Comparison

| Library | Speed (10-page PDF) | Memory | Accuracy |
|---------|---------------------|--------|----------|
| PyMuPDF | 0.5s | Low | Good |
| pdf2image | 2s | Medium | N/A (images) |
| pdfplumber | 1.5s | Low | Good (tables) |
| pypdf | 0.3s | Low | Basic |
| Unstructured | 5s | High | Excellent |
| docling | 8s | High | Excellent |
| marker-pdf | 10s | Very High | Best (academic) |

**Recommendation**: Start with **PyMuPDF** for speed, add **pdfplumber** for table-heavy docs, consider **docling** for complex enterprise documents.

### Why DuckDB over SQLite?

DuckDB is an excellent choice for document extraction results:
- **Columnar storage**: Efficient for analytical queries on extraction data
- **Native Parquet/CSV export**: Easy to export results for analysis
- **Fast aggregations**: Quick summaries across extracted documents
- **Python-native**: `pip install duckdb`, works seamlessly with pandas
- **Embedded**: No server setup, single file like SQLite but faster for analytics

```python
import duckdb

# Store extraction results
conn = duckdb.connect('extractions.duckdb')
conn.execute("""
    INSERT INTO extractions (doc_hash, vendor, amount, date, raw_json)
    VALUES (?, ?, ?, ?, ?)
""", [doc_hash, result.vendor_name, result.total_amount, result.date, json.dumps(result)])

# Analytics queries are fast
totals = conn.execute("""
    SELECT vendor, SUM(amount) as total
    FROM extractions
    GROUP BY vendor
""").fetchdf()  # Returns pandas DataFrame directly
```

### Hardware Requirements

For Qwen2-VL-7B:
- **Minimum**: 8GB RAM, CPU-only (slow, ~30s/doc)
- **Recommended**: 8GB+ VRAM GPU (fast, ~3s/doc)
- **Mac M1/M2/M3**: Works great with Metal acceleration

### Cost Breakdown (Monthly)

| Item | Current (Gemini) | Proposed (Local) |
|------|-----------------|------------------|
| LLM API | ~$3-5/month | $0 |
| Infrastructure | $0 | $0 |
| Storage | $0 | $0 |
| **Total** | ~$3-5/month | **$0** |

---

## Verification Steps

1. **Test Ollama locally**:
   ```bash
   ollama run qwen2-vl:7b
   # Try: "Extract invoice details from this image"
   ```

2. **Benchmark accuracy**: Compare 10 docs between Ollama and Gemini

3. **Measure latency**: Ensure <10s extraction time locally

---

## Next Actions

1. **Install Ollama** and pull Qwen2-VL model
2. **Create simple FastAPI backend** with extraction endpoint
3. **Test extraction quality** on your financial documents
4. **Integrate with React frontend** (replace direct Gemini calls)

# Requirements: DocuExtract AI

**Defined:** 2026-02-10
**Core Value:** Users can upload any supported document and get clean, structured JSON data extracted automatically

## v1 Requirements

### Extraction Pipeline

- [x] **EXTR-01**: User can upload a PDF or image document via the web UI
- [x] **EXTR-02**: System automatically classifies the document type (Invoice, Receipt, Bill, Bank Statement, EOB, Research Paper, Financial Report)
- [x] **EXTR-03**: System extracts structured data using type-specific prompts
- [ ] **EXTR-04**: Extraction results are validated and confidence scores are meaningful
- [ ] **EXTR-05**: User can re-extract a document with a different model or settings

### Data Storage

- [x] **DATA-01**: Extracted data is persisted in DuckDB with full schema
- [x] **DATA-02**: Duplicate documents are detected and rejected by content hash
- [ ] **DATA-03**: User can view all past extractions with filtering (date, vendor, type)
- [x] **DATA-04**: User can export extractions to CSV

### User Interface

- [x] **UI-01**: User can drag-and-drop or browse to upload documents
- [x] **UI-02**: User can see extraction results in a structured table
- [x] **UI-03**: User can manage multiple files in a sidebar
- [ ] **UI-04**: User can view detailed extraction data for a single document

### Quality & Testing

- [ ] **QUAL-01**: All 7 document types tested end-to-end with real documents
- [ ] **QUAL-02**: Tests pass and cover core backend functionality
- [ ] **QUAL-03**: Documentation accurately reflects the current project

## v2 Requirements

### Corrections

- **CORR-01**: User can manually correct extraction errors
- **CORR-02**: System learns from corrections to improve future extractions
- **CORR-03**: Corrections are tracked and auditable

### Export

- **EXPRT-01**: User can export to Parquet format
- **EXPRT-02**: User can export selected extractions (not just all)

### Document Types

- **DTYPE-01**: Support for additional document types (medical bills, tax forms)
- **DTYPE-02**: Custom document type definitions by user

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cloud LLM processing | Privacy-first design, local-only |
| Multi-user / auth | Personal-use tool |
| Mobile app | Web-first |
| customtkinter GUI | Replaced by React frontend |
| Real-time collaboration | Single-user tool |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EXTR-01 | Phase 1 | Complete |
| EXTR-02 | Phase 1 | Complete |
| EXTR-03 | Phase 1 | Complete |
| EXTR-04 | Phase 3 | Pending |
| EXTR-05 | Phase 3 | Pending |
| DATA-01 | Phase 2 | Complete |
| DATA-02 | Phase 2 | Complete |
| DATA-03 | Phase 3 | Pending |
| DATA-04 | Phase 2 | Complete |
| UI-01 | Phase 2 | Complete |
| UI-02 | Phase 2 | Complete |
| UI-03 | Phase 2 | Complete |
| UI-04 | Phase 3 | Pending |
| QUAL-01 | Phase 3 | Pending |
| QUAL-02 | Phase 3 | Pending |
| QUAL-03 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓
- Complete: 10
- Pending: 6

---
*Requirements defined: 2026-02-10*
*Last updated: 2026-02-10 after GSD initialization (brownfield)*

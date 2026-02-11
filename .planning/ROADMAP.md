# Roadmap: DocuExtract AI

## Overview

DocuExtract AI has completed its core extraction pipeline and web frontend. The remaining work focuses on testing, documentation cleanup, code hygiene, and building the correction/learning system.

## Phases

- [x] **Phase 1: Extraction Pipeline** - Three-stage OCR → classify → extract with 7 document types
- [x] **Phase 2: Storage & Frontend** - DuckDB persistence, React web UI, file management
- [ ] **Phase 3: Testing & Polish** - End-to-end validation, docs update, dead code cleanup
- [ ] **Phase 4: Correction System** - User corrections, pattern learning, extraction improvement

## Phase Details

### Phase 1: Extraction Pipeline
**Goal**: Working document extraction from PDF/image to structured JSON
**Depends on**: Nothing (first phase)
**Requirements**: EXTR-01, EXTR-02, EXTR-03
**Success Criteria** (what must be TRUE):
  1. User can upload a PDF and receive structured JSON back
  2. System correctly identifies document type from 7 supported types
  3. Extraction uses type-specific prompts for better accuracy
**Plans**: Complete

### Phase 2: Storage & Frontend
**Goal**: Persistent storage with deduplication and a usable web interface
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-04, UI-01, UI-02, UI-03
**Success Criteria** (what must be TRUE):
  1. Extracted data persists in DuckDB across sessions
  2. Re-uploading the same document is detected and rejected
  3. User can manage multiple documents via the web UI
**Plans**: Complete

### Phase 3: Testing & Polish
**Goal**: Validate extraction quality, update documentation, clean up codebase
**Depends on**: Phase 2
**Requirements**: EXTR-04, EXTR-05, DATA-03, UI-04, QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. All 7 document types tested with real documents and results verified
  2. Documentation (PRD, README, TODO) accurately describes the generalized tool
  3. No dead code or empty directories remain
  4. Test suite passes with meaningful coverage
  5. User can filter and browse past extractions
**Plans**: 3 plans in 2 waves

Plans:
- [ ] 03-01: Fix and validate test suite (Wave 1)
- [ ] 03-02: Documentation overhaul — update PRD, README, TODO, AGENTS (Wave 1)
- [ ] 03-03: Code cleanup — remove dead dirs, consolidate models (Wave 2, depends on 03-01)

### Phase 4: Correction System
**Goal**: User can correct extraction errors and system learns from corrections
**Depends on**: Phase 3
**Requirements**: CORR-01, CORR-02, CORR-03 (v2 — stretch)
**Success Criteria** (what must be TRUE):
  1. User can edit extracted fields in the UI
  2. Corrections are saved and override original extraction
  3. System uses correction patterns to improve future extractions
**Plans**: 3 plans in 2 waves

Plans:
- [ ] 04-01: Backend corrections support — updates & audit trail (Wave 1)
- [ ] 04-02: Frontend inline editing — refactor ResultsTable & add edit mode (Wave 2, depends on 04-01)
- [ ] 04-03: Learning system — pattern storage & application logic (Wave 2, depends on 04-01)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 1. Extraction Pipeline | ✓ | Complete | 2026-02-10 |
| 2. Storage & Frontend | ✓ | Complete | 2026-02-10 |
| 3. Testing & Polish | 0/3 | Not started | - |
| 4. Correction System | 0/3 | Not started | - |

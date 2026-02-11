# DocuExtract AI

## What This Is

A local-first document extraction tool that converts financial documents (invoices, receipts, bank statements, insurance EOBs), academic research papers, and financial reports into structured data using vision LLMs. All processing runs locally via Ollama — no data leaves the machine.

## Core Value

Users can upload any supported document and get clean, structured JSON data extracted automatically with no manual data entry and no cloud dependency.

## Requirements

### Validated

<!-- Shipped and confirmed working. -->

- ✓ FastAPI backend with extract/list/export/health endpoints — initial commit
- ✓ Three-stage extraction pipeline (DeepSeek OCR2 → Qwen3 classify → Qwen3 extract) — initial commit
- ✓ PDF parser with text/vision/hybrid strategies (PyMuPDF, pdfplumber, pdf2image) — initial commit
- ✓ DuckDB storage with extractions and line_items tables, deduplication by doc hash — initial commit
- ✓ React 19 frontend with file upload, results table, file sidebar — initial commit
- ✓ Support for 7 document types: Invoice, Receipt, Bill, Bank Statement, Insurance EOB, Research Paper, Financial Report — initial commit
- ✓ Test suite covering API, database, extraction, models, and PDF parser — initial commit

### Active

<!-- Current scope. Building toward these. -->

- [ ] End-to-end testing with real documents across all 7 types
- [ ] Documentation update to match generalized scope (docs/ still references EOB-only)
- [ ] Clean up stale code (old Pydantic models, empty directories)
- [ ] Correction & learning system for extraction errors

### Out of Scope

<!-- Explicit boundaries. -->

- customtkinter GUI — abandoned in favor of React web frontend
- Multi-user support — personal use only
- Cloud LLM fallback — local-only processing is a core principle
- Mobile app — web-first

## Context

This project evolved from an EOB-specific medical expense tracker to a generalized document extractor. The original PRD, README, and TODO in `docs/` still describe the old EOB-only scope and need updating.

The archived folder (`docuxtractor_archived/`) contains two prior iterations that informed the current design.

The extraction pipeline uses a two-step classify-then-extract approach that was added during generalization (conversation 759c6751).

## Constraints

- **Runtime**: All LLM inference must run locally via Ollama — privacy-first
- **Tech stack**: Python 3.11+ backend, React 19 + TypeScript frontend, DuckDB storage
- **File size**: 10MB upload limit per document
- **Models**: Requires ~7GB disk for DeepSeek-OCR + Qwen3-VL models

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pivoted from EOB-only to generalized extractor | More broadly useful tool | ✓ Good |
| React frontend over customtkinter | Modern web UI, cross-platform | ✓ Good |
| Three-stage pipeline (OCR → classify → extract) | Type-specific prompts improve accuracy | ✓ Good |
| DuckDB over SQLite | Columnar storage better for analytical queries | ✓ Good |
| Local-only via Ollama | Privacy is non-negotiable for financial docs | ✓ Good |

---
*Last updated: 2026-02-10 after project status audit and GSD initialization*

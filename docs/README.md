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
# EOB Medical Expense Tracker

Extract structured data from health insurance Explanation of Benefits (EOB) PDFs using local vision LLMs, and track medical expenses with a modern GUI application.

## Features

- **PDF → Image conversion** with configurable DPI (300 DPI default for optimal OCR)
- **Vision LLM extraction** supporting multiple models:
  - `qwen2.5vl:3b` - Fast, good for structured JSON output (2GB)
  - `deepseek-ocr` - Specialized for document OCR (6.7GB)
  - `richardyoung/olmocr2:7b-q8` - Fine-tuned for complex documents (8.8GB)
- **DuckDB storage** with full schema for:
  - Members (people on plan)
  - Documents (EOB statements)
  - Claims (services rendered)
  - Line items (individual charges)
  - Accumulators (deductibles, OOP max tracking)
- **Modern GUI** built with customtkinter:
  - Import view with batch processing and parallel extraction
  - Claims view with sorting, filtering, and detail popups
  - Dashboard with summary cards, progress bars, and charts
- **CLI tools** for batch processing and querying
- **Parallel processing** for faster batch imports

## Prerequisites

### macOS
```bash
# Install poppler (required for pdf2image)
brew install poppler

# Install Ollama
brew install ollama

# Install uv (Python package manager)
brew install uv
```

### Linux
```bash
sudo apt-get install poppler-utils
curl -fsSL https://ollama.com/install.sh | sh

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

### Using uv (Recommended)

```bash
# Clone or navigate to the project directory

# Sync dependencies and create virtual environment
uv sync

# Activate the virtual environment (if needed)
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Pull vision models (choose one or more)
ollama pull qwen2.5vl:3b           # 2GB, fast
ollama pull deepseek-ocr            # 6.7GB, OCR specialist
ollama pull richardyoung/olmocr2:7b-q8  # 8.8GB, highest accuracy
```

### Using pip (Legacy)

```bash
pip install -r requirements.txt
```

## Usage

### GUI Application

Launch the GUI application:

```bash
# Using uv
uv run python main.py

# Or if virtual environment is activated
python main.py
```

**Import View:**
1. Click "Select Folder" to choose a folder containing EOB PDFs
2. Select a vision model from the dropdown
3. Click "Preview Selected" to test extraction on the first PDF
4. Click "Import All" to batch process all PDFs (uses parallel processing)

**Claims View:**
1. View all claims in a sortable table
2. Filter by provider, date range
3. Click a row to see line item details
4. Export to CSV for external analysis

**Dashboard View:**
1. View YTD spending summary cards
2. Monitor deductible and OOP max progress bars
3. See spending trends in charts (by month, by provider)
4. Click "Refresh" to reload data

### CLI Tools

#### Extract EOBs

```bash
# Using uv entry points
uv run eob-extract /path/to/eob/pdfs --db data/eob.duckdb

# Or directly
python -m cli.extract /path/to/eob/pdfs --db data/eob.duckdb

# Use a specific model
uv run eob-extract /path/to/eob/pdfs --model deepseek-ocr

# Process a single PDF
uv run eob-extract /path/to/single_eob.pdf

# Higher DPI for small text
uv run eob-extract /path/to/eobs --dpi 300
```

#### Query Data

```bash
# Database summary
uv run eob-query data/eob.duckdb summary

# Spending by member
uv run eob-query data/eob.duckdb spending
uv run eob-query data/eob.duckdb spending --year 2025

# List claims
uv run eob-query data/eob.duckdb claims
uv run eob-query data/eob.duckdb claims --member "John"

# Deductible/OOP max status
uv run eob-query data/eob.duckdb accumulators

# Tax year summary
uv run eob-query data/eob.duckdb tax --year 2025

# Custom SQL
uv run eob-query data/eob.duckdb sql "SELECT * FROM claims ORDER BY service_date DESC LIMIT 10"
```

## Architecture

### Project Structure

```
eob-tracker/
├── pyproject.toml          # uv dependencies and project config
├── main.py                 # GUI app entry point
├── extractor/
│   ├── pdf_to_images.py    # PDF → PNG conversion
│   ├── vision_extract.py   # Ollama extraction with retry logic
│   └── prompts.py          # Page-specific extraction prompts
├── models/
│   └── schemas.py          # Pydantic data models
├── database/
│   └── db.py               # DuckDB operations (CRUD, queries)
├── gui/
│   ├── app.py              # Main window and navigation
│   ├── import_view.py      # Import interface with parallel processing
│   ├── claims_view.py      # Claims table with filtering
│   └── dashboard.py        # Analytics dashboard
├── cli/
│   ├── extract.py          # CLI extraction tool
│   └── query.py            # CLI query tool
└── data/
    └── eob.duckdb          # Database file (gitignored)
```

### Data Flow

```
PDF Files → pdf_to_images → Vision LLM (Ollama) → JSON Parsing → 
Pydantic Validation → DuckDB Storage → GUI/CLI Display
```

### Extraction Pipeline

1. **PDF Conversion**: Convert PDF pages to PNG images at specified DPI
2. **Page Classification**: Determine page type (summary, accumulators, claims)
3. **Vision Extraction**: Send images to Ollama with page-specific prompts
4. **JSON Parsing**: Extract JSON from LLM response, handle markdown code blocks
5. **Validation**: Validate against Pydantic schemas
6. **Database Storage**: Upsert data with deduplication by claim_id
7. **Parallel Processing**: Process multiple PDFs concurrently (up to 4 workers)

### Database Schema

```
members
├── member_id (PK)
├── member_name
├── relationship
└── first_seen_date

documents
├── document_id (PK)
├── statement_date
├── member_id (FK)
├── group_id
├── source_file
├── model_used
└── extracted_at

claims
├── claim_id (PK)
├── document_id (FK)
├── member_id (FK)
├── provider_name
├── service_date
├── in_network
├── total_billed
├── total_allowed
├── total_insurance_paid
└── total_patient_responsibility

line_items
├── line_item_id (PK) -- format: {claim_id}_{line_number}
├── claim_id (FK)
├── line_number
├── service_date
├── service_description
├── procedure_code
├── reason_code
├── billed_amount
├── allowed_amount
├── insurance_paid
├── copay
├── deductible_applied
├── coinsurance
├── not_covered
└── patient_responsibility

accumulators
├── accumulator_id (PK)
├── document_id (FK)
├── snapshot_date
├── plan_year
├── member_id (FK, nullable for family)
├── coverage_tier (individual/family)
├── network_type (in_network/out_of_network)
├── accumulator_type (deductible/oop_max)
├── limit_amount
├── applied_amount
└── remaining_amount
```

## Example Queries

### Track deductible progression over time
```sql
SELECT 
    snapshot_date,
    applied_amount,
    remaining_amount,
    applied_amount - LAG(applied_amount) OVER (ORDER BY snapshot_date) as change
FROM accumulators
WHERE coverage_tier = 'individual' 
  AND accumulator_type = 'deductible'
  AND network_type = 'in_network'
ORDER BY snapshot_date;
```

### Find claims with high patient responsibility
```sql
SELECT 
    c.service_date,
    c.provider_name,
    l.service_description,
    l.billed_amount,
    l.patient_responsibility,
    l.reason_code
FROM line_items l
JOIN claims c ON l.claim_id = c.claim_id
WHERE l.patient_responsibility > 100
ORDER BY l.patient_responsibility DESC;
```

### Annual summary for tax deduction
```sql
SELECT 
    YEAR(c.service_date) as year,
    SUM(l.patient_responsibility) as total_medical,
    SUM(l.copay) as copays,
    SUM(l.deductible_applied) as deductible,
    SUM(l.coinsurance) as coinsurance
FROM line_items l
JOIN claims c ON l.claim_id = c.claim_id
GROUP BY YEAR(c.service_date)
ORDER BY year;
```

## Troubleshooting

### PDF conversion fails
- Ensure poppler is installed: `brew install poppler` (macOS) or `apt install poppler-utils` (Linux)
- Try lower DPI if memory is an issue: `--dpi 200`

### Model not found
- Pull the model first: `ollama pull qwen2.5vl:3b`
- Check Ollama is running: `ollama list`

### Poor extraction quality
- Try higher DPI: `--dpi 300`
- Try a different model (olmocr2 is most accurate but slowest)
- Check the raw_extractions table for debugging

### JSON parsing errors
- The raw output is stored in `raw_extractions` table
- Query with: `SELECT raw_output FROM raw_extractions WHERE document_id = '...'`

### GUI issues
- Ensure customtkinter is installed: `uv sync`
- Check database path is correct (default: `data/eob.duckdb`)
- Verify Ollama is running before importing PDFs

### uv sync fails
- Ensure Python 3.11+ is installed: `python --version`
- Try updating uv: `brew upgrade uv` or reinstall from https://astral.sh/uv

## Model Comparison

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| qwen2.5vl:3b | 2GB | Fast | Good | Quick extraction, structured JSON |
| deepseek-ocr | 6.7GB | Medium | Good | Document-heavy EOBs |
| olmocr2:7b-q8 | 8.8GB | Slow | Best | Complex tables, small text |

Start with `qwen2.5vl:3b`. If accuracy is insufficient, try `olmocr2`.

## Development

### Running Tests

```bash
# Run with uv
uv run pytest

# Or activate venv first
source .venv/bin/activate
pytest
```

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev pytest
```

### Project Management

This project uses **beads** (bd) for task tracking:

```bash
bd ready          # Find available work
bd show <id>      # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>     # Complete work
bd sync           # Sync with git
```

## Privacy

- All processing runs locally via Ollama
- No data leaves the machine
- No cloud APIs required
- Database stored locally in `data/eob.duckdb`

## License

MIT License - See LICENSE file for details

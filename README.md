# DocuExtract AI

A local-first financial document extraction tool that converts invoices, receipts, bank statements, and insurance EOBs into structured data using vision LLMs.

## Architecture

**Current Stack:**
- **Frontend**: React 19 + TypeScript + Vite
- **Backend**: FastAPI (Python) - *Coming soon*
- **LLM**: Ollama (Qwen2-VL-7B) with Gemini Flash fallback
- **Storage**: DuckDB (local database)
- **PDF Processing**: PyMuPDF, pdfplumber, pdf2image

## Features

- 📄 Extract structured data from financial documents (invoices, receipts, statements, EOBs)
- 🔒 Local-first processing with Ollama (privacy-preserving)
- 🚀 Fast extraction with vision LLMs
- 💾 Local database storage with DuckDB
- 📊 CSV/Parquet export
- 🔄 Document deduplication
- ✏️ Correction system with pattern learning

## Project Status

**Phase**: Backend Implementation (See [Implementation Plan](./fluttering-snuggling-comet.md))

The frontend is functional and currently uses direct Gemini API calls. The backend is being implemented according to the architecture plan.

## Quick Start

### Frontend (Current)

```bash
npm install
npm run dev
```

### Backend (In Progress)

See [fluttering-snuggling-comet.md](./fluttering-snuggling-comet.md) for detailed implementation steps.

## Development Roadmap

1. ✅ Frontend MVP with Gemini API
2. 🔄 Backend API with FastAPI
3. 🔄 Local LLM integration (Ollama)
4. 🔄 DuckDB storage
5. 🔄 Correction & learning system

## License

MIT

# DocuExtract AI

A local-first financial document extraction tool that converts invoices, receipts, bank statements, and insurance EOBs into structured data using vision LLMs.

## Architecture

**Current Stack:**
- **Frontend**: React 19 + TypeScript + Vite
- **Backend**: FastAPI (Python) - *Coming soon*
- **LLM**: Ollama (Qwen3-VL) - local-only processing
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

**Phase**: Backend Complete - Ready for Testing

The backend API is implemented and ready to use. Frontend has been updated to use the backend API.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) package manager
- [Ollama](https://ollama.com) (for local LLM)
- Poppler (for PDF to image conversion)

### Setup

1. **Install Python dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

2. **Install Poppler (macOS):**
   ```bash
   brew install poppler
   ```

3. **Install Ollama and pull Qwen3-VL model:**
   ```bash
   # Install Ollama
   brew install ollama  # macOS
   # or: curl -fsSL https://ollama.com/install.sh | sh  # Linux
   
   # Start Ollama server
   ollama serve
   
   # In another terminal, pull the vision model
   ollama pull qwen3-vl
   ```

4. **Set up environment variables (optional):**
   ```bash
   # Create .env file
   echo "VITE_BACKEND_URL=http://localhost:8000" > .env
   ```

5. **Install frontend dependencies:**
   ```bash
   npm install
   ```

### Running the Application

1. **Start the backend:**
   ```bash
   source .venv/bin/activate
   ./run_backend.sh
   # Or: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend (in another terminal):**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5173` (or the port shown by Vite)

## Development Roadmap

1. ✅ Frontend MVP
2. ✅ Backend API with FastAPI
3. ✅ Local LLM integration (Ollama)
4. ✅ DuckDB storage
5. ✅ Frontend integration
6. 🔄 Correction & learning system (planned)

## License

MIT

"""PDF parsing utilities using PyMuPDF, pdfplumber, and pdf2image"""
import io
from typing import List, Dict, Any, Optional
from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber
from pdf2image import convert_from_bytes
from PIL import Image


def detect_file_type(file_bytes: bytes, filename: str) -> str:
    """Detect if file is PDF or image"""
    if filename.lower().endswith(('.pdf',)):
        return 'pdf'
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
        return 'image'
    else:
        # Check magic bytes
        if file_bytes.startswith(b'%PDF'):
            return 'pdf'
        elif file_bytes.startswith(b'\x89PNG'):
            return 'image'
        elif file_bytes.startswith(b'\xff\xd8\xff'):
            return 'image'
    return 'unknown'


def extract_text(pdf_bytes: bytes) -> List[str]:
    """Extract text from PDF using PyMuPDF (fast)"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        pages_text.append(text)
    doc.close()
    return pages_text


def extract_tables(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """Extract tables from PDF using pdfplumber"""
    tables = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()
            for table in page_tables:
                tables.append({
                    "page": page_num + 1,
                    "table": table
                })
    return tables


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[Image.Image]:
    """Convert PDF pages to PIL Images for vision LLM processing"""
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        return images
    except Exception as e:
        raise ValueError(f"Failed to convert PDF to images: {e}")


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string"""
    import base64
    from io import BytesIO
    
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")


def parse_document(
    file_bytes: bytes,
    filename: str,
    strategy: str = "vision"
) -> Dict[str, Any]:
    """
    Parse document and return preprocessed content for LLM
    
    Args:
        file_bytes: Raw file bytes
        filename: Original filename
        strategy: "text", "vision", or "hybrid"
    
    Returns:
        Dict with parsed content ready for LLM processing
    """
    file_type = detect_file_type(file_bytes, filename)
    
    result = {
        "file_type": file_type,
        "filename": filename,
        "strategy": strategy
    }
    
    if file_type == "pdf":
        if strategy in ("text", "hybrid"):
            result["text"] = extract_text(file_bytes)
            result["tables"] = extract_tables(file_bytes)
        
        if strategy in ("vision", "hybrid"):
            images = pdf_to_images(file_bytes)
            result["images"] = [image_to_base64(img) for img in images]
            result["image_count"] = len(images)
    
    elif file_type == "image":
        # For images, convert to base64
        result["images"] = [image_to_base64(Image.open(io.BytesIO(file_bytes)))]
        result["image_count"] = 1
    
    return result

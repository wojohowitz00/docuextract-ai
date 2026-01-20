"""LLM extraction module with Ollama + Gemini fallback"""
import os
import json
import base64
from typing import Dict, Any, Optional, List
from PIL import Image
import io
import ollama
from google import genai
from .models import ExtractedData, DocumentType


# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


EXTRACTION_PROMPT = """
Analyze this image of a financial document. 
Extract all relevant data points and return a strictly formatted JSON object.

The JSON structure must be as follows:
{{
  "documentType": "Invoice" | "Receipt" | "Bank Statement" | "Insurance EOB" | "Unknown",
  "vendorName": "string",
  "vendorAddress": "string (address of vendor if available)",
  "invoiceNumber": "string",
  "date": "YYYY-MM-DD",
  "dueDate": "YYYY-MM-DD (optional)",
  "totalAmount": number,
  "taxAmount": number,
  "currency": "string (e.g. USD)",
  "lineItems": [
    {{
      "description": "string",
      "quantity": number,
      "unitPrice": number,
      "total": number,
      "sku": "string (optional)"
    }}
  ],
  "summary": "string (1 sentence summary)"
}}

Rules:
1. Ensure numerical values are parsed correctly as numbers.
2. If a field is missing, use null or 0 (for numbers) as appropriate.
3. Format dates as YYYY-MM-DD.
4. Output ONLY the valid JSON string. Do not include markdown formatting like ```json.
"""


def calculate_confidence(extracted_data: Dict[str, Any]) -> float:
    """Calculate confidence score based on required fields"""
    required_fields = ["vendorName", "totalAmount", "date"]
    present_fields = sum(1 for field in required_fields if extracted_data.get(field))
    
    base_score = present_fields / len(required_fields)
    
    # Bonus for having line items
    if extracted_data.get("lineItems"):
        base_score += 0.1
    
    # Bonus for having invoice number
    if extracted_data.get("invoiceNumber"):
        base_score += 0.1
    
    return min(base_score, 1.0)


def parse_json_response(text: str) -> Dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks"""
    # Remove markdown code blocks if present
    if "```" in text:
        text = text.replace("```json", "").replace("```", "")
    
    # Find JSON object bounds
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    
    if first_brace != -1 and last_brace != -1:
        text = text[first_brace:last_brace + 1]
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}")


async def ollama_extract(images: List[str], prompt: str = EXTRACTION_PROMPT) -> Dict[str, Any]:
    """Extract data using local Ollama Qwen2-VL model"""
    try:
        # Ollama vision models expect images as base64 strings
        # For Qwen2-VL, we can send multiple images in a single message
        # Process first image (can be extended for multi-page documents)
        response = ollama.chat(
            model="qwen3-vl",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": images[:1]  # Send first image, can extend for multi-page
            }]
        )
        
        text = response["message"]["content"]
        extracted = parse_json_response(text)
        
        # Calculate confidence
        confidence = calculate_confidence(extracted)
        
        return {
            "data": extracted,
            "confidence": confidence,
            "provider": "ollama"
        }
    except Exception as e:
        # Check if it's a model not found error
        if "model" in str(e).lower() or "not found" in str(e).lower():
            raise ValueError(f"Ollama model 'qwen3-vl' not found. Please run: ollama pull qwen3-vl")
        raise ValueError(f"Ollama extraction failed: {e}")


async def gemini_extract(images: List[str], prompt: str = EXTRACTION_PROMPT) -> Dict[str, Any]:
    """Extract data using Gemini API"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Convert base64 to PIL Images for Gemini
        image_parts = []
        for img_base64 in images:
            img_bytes = base64.b64decode(img_base64)
            img = Image.open(io.BytesIO(img_bytes))
            image_parts.append(img)
        
        # Build content with images
        contents = [prompt]
        for img in image_parts:
            contents.append(img)
        
        # Use the new genai API
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents
        )
        
        text = response.text
        if not text:
            raise ValueError("No response from Gemini")
        
        extracted = parse_json_response(text)
        
        # Calculate confidence
        confidence = calculate_confidence(extracted)
        
        return {
            "data": extracted,
            "confidence": confidence,
            "provider": "gemini"
        }
    except Exception as e:
        raise ValueError(f"Gemini extraction failed: {e}")


async def extract_document(
    file_bytes: bytes,
    filename: str,
    prefer_local: bool = True
) -> Dict[str, Any]:
    """
    Extract document data with Ollama + Gemini fallback
    
    Args:
        file_bytes: Raw file bytes
        filename: Original filename
        prefer_local: Try Ollama first if True
    
    Returns:
        Dict with extracted data, confidence, and provider
    """
    from .pdf_parser import parse_document
    
    # Parse document to get images
    parsed = parse_document(file_bytes, filename, strategy="vision")
    
    if not parsed.get("images"):
        raise ValueError("No images extracted from document")
    
    images = parsed["images"]
    
    # Try local Ollama first if preferred
    if prefer_local:
        try:
            result = await ollama_extract(images)
            # If confidence is good enough, return it
            if result["confidence"] >= 0.8:
                return result
        except Exception:
            # Fall through to Gemini
            pass
    
    # Fallback to Gemini
    try:
        return await gemini_extract(images)
    except Exception as e:
        # If both fail, raise error
        raise ValueError(f"All extraction methods failed. Last error: {e}")

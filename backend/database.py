"""DuckDB database operations for storing extraction results"""
import duckdb
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


DB_PATH = Path("extractions.duckdb")


def init_database() -> duckdb.DuckDBPyConnection:
    """Initialize database and create tables if they don't exist"""
    conn = duckdb.connect(str(DB_PATH))
    
    # Create extractions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS extractions (
            id VARCHAR PRIMARY KEY,
            doc_hash VARCHAR UNIQUE,
            filename VARCHAR,
            document_type VARCHAR,
            vendor_name VARCHAR,
            total_amount DECIMAL(15,2),
            currency VARCHAR(3),
            date DATE,
            due_date DATE,
            tax_amount DECIMAL(15,2),
            invoice_number VARCHAR,
            vendor_address VARCHAR,
            summary TEXT,
            raw_json JSON,
            confidence DECIMAL(3,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create line_items table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS line_items (
            id VARCHAR PRIMARY KEY,
            extraction_id VARCHAR,
            description VARCHAR,
            quantity DECIMAL(10,2),
            unit_price DECIMAL(15,2),
            total DECIMAL(15,2),
            sku VARCHAR,
            FOREIGN KEY (extraction_id) REFERENCES extractions(id)
        )
    """)
    
    # Create index on doc_hash for fast deduplication lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_doc_hash ON extractions(doc_hash)
    """)
    
    # Create index on created_at for date range queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at ON extractions(created_at)
    """)
    
    return conn


def generate_doc_hash(file_bytes: bytes) -> str:
    """Generate SHA-256 hash of document for deduplication"""
    return hashlib.sha256(file_bytes).hexdigest()


def save_extraction(
    conn: duckdb.DuckDBPyConnection,
    extraction_id: str,
    doc_hash: str,
    filename: str,
    extracted_data: Dict[str, Any],
    confidence: float = 1.0
) -> str:
    """Save extraction result to database"""
    # Insert extraction
    conn.execute("""
        INSERT INTO extractions (
            id, doc_hash, filename, document_type, vendor_name,
            total_amount, currency, date, due_date, tax_amount,
            invoice_number, vendor_address, summary, raw_json, confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        extraction_id,
        doc_hash,
        filename,
        extracted_data.get("documentType", "Unknown"),
        extracted_data.get("vendorName", ""),
        extracted_data.get("totalAmount", 0.0),
        extracted_data.get("currency", "USD"),
        extracted_data.get("date"),
        extracted_data.get("dueDate"),
        extracted_data.get("taxAmount", 0.0),
        extracted_data.get("invoiceNumber", ""),
        extracted_data.get("vendorAddress"),
        extracted_data.get("summary"),
        json.dumps(extracted_data),
        confidence
    ])
    
    # Insert line items
    line_items = extracted_data.get("lineItems", [])
    for idx, item in enumerate(line_items):
        line_item_id = f"{extraction_id}_line_{idx}"
        conn.execute("""
            INSERT INTO line_items (
                id, extraction_id, description, quantity,
                unit_price, total, sku
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            line_item_id,
            extraction_id,
            item.get("description", ""),
            item.get("quantity", 0.0),
            item.get("unitPrice", 0.0),
            item.get("total", 0.0),
            item.get("sku")
        ])
    
    return extraction_id


def get_extraction(conn: duckdb.DuckDBPyConnection, extraction_id: str) -> Optional[Dict[str, Any]]:
    """Get extraction by ID with line items"""
    result = conn.execute("""
        SELECT * FROM extractions WHERE id = ?
    """, [extraction_id]).fetchone()
    
    if not result:
        return None
    
    # Get line items
    line_items = conn.execute("""
        SELECT description, quantity, unit_price, total, sku
        FROM line_items
        WHERE extraction_id = ?
        ORDER BY id
    """, [extraction_id]).fetchall()
    
    # Reconstruct extraction data
    extraction = {
        "id": result[0],
        "documentType": result[3],
        "vendorName": result[4],
        "totalAmount": float(result[5]) if result[5] else 0.0,
        "currency": result[6],
        "date": result[7].isoformat() if result[7] else None,
        "dueDate": result[8].isoformat() if result[8] else None,
        "taxAmount": float(result[9]) if result[9] else 0.0,
        "invoiceNumber": result[10],
        "vendorAddress": result[11],
        "summary": result[12],
        "lineItems": [
            {
                "description": item[0],
                "quantity": float(item[1]) if item[1] else 0.0,
                "unitPrice": float(item[2]) if item[2] else 0.0,
                "total": float(item[3]) if item[3] else 0.0,
                "sku": item[4]
            }
            for item in line_items
        ]
    }
    
    return extraction


def check_duplicate(conn: duckdb.DuckDBPyConnection, doc_hash: str) -> Optional[Dict[str, Any]]:
    """Check if document hash already exists, return existing extraction if found"""
    result = conn.execute("""
        SELECT id FROM extractions WHERE doc_hash = ?
    """, [doc_hash]).fetchone()
    
    if result:
        return get_extraction(conn, result[0])
    return None


def list_extractions(
    conn: duckdb.DuckDBPyConnection,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    vendor: Optional[str] = None,
    doc_type: Optional[str] = None,
    offset: int = 0,
    limit: int = 100
) -> tuple[List[Dict[str, Any]], int]:
    """List extractions with filters and pagination"""
    conditions = []
    params = []
    
    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)
    if vendor:
        conditions.append("vendor_name ILIKE ?")
        params.append(f"%{vendor}%")
    if doc_type:
        conditions.append("document_type = ?")
        params.append(doc_type)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Get total count
    count_result = conn.execute(f"""
        SELECT COUNT(*) FROM extractions WHERE {where_clause}
    """, params).fetchone()
    total = count_result[0] if count_result else 0
    
    # Get paginated results
    params.extend([limit, offset])
    results = conn.execute(f"""
        SELECT id, filename, document_type, vendor_name, total_amount,
               currency, date, created_at
        FROM extractions
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, params).fetchall()
    
    extractions = [
        {
            "id": r[0],
            "filename": r[1],
            "documentType": r[2],
            "vendorName": r[3],
            "totalAmount": float(r[4]) if r[4] else 0.0,
            "currency": r[5],
            "date": r[6].isoformat() if r[6] else None,
            "createdAt": r[7].isoformat() if r[7] else None
        }
        for r in results
    ]
    
    return extractions, total


def export_to_csv(conn: duckdb.DuckDBPyConnection, extraction_ids: Optional[List[str]] = None) -> bytes:
    """Export extractions to CSV format"""
    if extraction_ids:
        placeholders = ",".join(["?"] * len(extraction_ids))
        query = f"""
            SELECT 
                e.id, e.filename, e.document_type, e.vendor_name,
                e.total_amount, e.currency, e.date, e.invoice_number,
                e.tax_amount, e.summary,
                l.description, l.quantity, l.unit_price, l.total, l.sku
            FROM extractions e
            LEFT JOIN line_items l ON e.id = l.extraction_id
            WHERE e.id IN ({placeholders})
            ORDER BY e.id, l.id
        """
        result = conn.execute(query, extraction_ids)
    else:
        result = conn.execute("""
            SELECT 
                e.id, e.filename, e.document_type, e.vendor_name,
                e.total_amount, e.currency, e.date, e.invoice_number,
                e.tax_amount, e.summary,
                l.description, l.quantity, l.unit_price, l.total, l.sku
            FROM extractions e
            LEFT JOIN line_items l ON e.id = l.extraction_id
            ORDER BY e.id, l.id
        """)
    
    # Convert to CSV
    csv_lines = []
    csv_lines.append("id,filename,document_type,vendor_name,total_amount,currency,date,invoice_number,tax_amount,summary,line_description,line_quantity,line_unit_price,line_total,line_sku")
    
    for row in result.fetchall():
        csv_line = ",".join([
            str(val).replace(",", ";") if val is not None else ""
            for val in row
        ])
        csv_lines.append(csv_line)
    
    return "\n".join(csv_lines).encode("utf-8")

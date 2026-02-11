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
    
    # Create extractions table — generalized for all document types
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
            account_number VARCHAR,
            billing_period VARCHAR,
            summary TEXT,
            -- Research paper fields
            title VARCHAR,
            authors TEXT,
            abstract TEXT,
            journal VARCHAR,
            doi VARCHAR,
            publication_date DATE,
            keywords TEXT,
            methodology TEXT,
            findings TEXT,
            -- Financial report fields
            company_name VARCHAR,
            report_type VARCHAR,
            report_period VARCHAR,
            revenue DECIMAL(15,2),
            expenses DECIMAL(15,2),
            net_income DECIMAL(15,2),
            key_metrics JSON,
            -- Metadata
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
    
    # Indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_doc_hash ON extractions(doc_hash)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at ON extractions(created_at)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_type ON extractions(document_type)
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
    doc_type = extracted_data.get("documentType", "Unknown")

    conn.execute("""
        INSERT INTO extractions (
            id, doc_hash, filename, document_type, vendor_name,
            total_amount, currency, date, due_date, tax_amount,
            invoice_number, vendor_address, account_number, billing_period,
            summary,
            title, authors, abstract, journal, doi,
            publication_date, keywords, methodology, findings,
            company_name, report_type, report_period,
            revenue, expenses, net_income, key_metrics,
            raw_json, confidence
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?
        )
    """, [
        extraction_id,
        doc_hash,
        filename,
        doc_type,
        extracted_data.get("vendorName", ""),
        extracted_data.get("totalAmount", 0.0),
        extracted_data.get("currency", "USD"),
        extracted_data.get("date"),
        extracted_data.get("dueDate"),
        extracted_data.get("taxAmount", 0.0),
        extracted_data.get("invoiceNumber", ""),
        extracted_data.get("vendorAddress"),
        extracted_data.get("accountNumber"),
        extracted_data.get("billingPeriod"),
        extracted_data.get("summary"),
        # Research paper
        extracted_data.get("title"),
        json.dumps(extracted_data.get("authors")) if extracted_data.get("authors") else None,
        extracted_data.get("abstract"),
        extracted_data.get("journal"),
        extracted_data.get("doi"),
        extracted_data.get("publicationDate"),
        json.dumps(extracted_data.get("keywords")) if extracted_data.get("keywords") else None,
        extracted_data.get("methodology"),
        extracted_data.get("findings"),
        # Financial report
        extracted_data.get("companyName"),
        extracted_data.get("reportType"),
        extracted_data.get("reportPeriod"),
        extracted_data.get("revenue"),
        extracted_data.get("expenses"),
        extracted_data.get("netIncome"),
        json.dumps(extracted_data.get("keyMetrics")) if extracted_data.get("keyMetrics") else None,
        # Metadata
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
    
    # Get column names
    columns = [desc[0] for desc in conn.description]
    row = dict(zip(columns, result))

    # Get line items
    line_items = conn.execute("""
        SELECT description, quantity, unit_price, total, sku
        FROM line_items
        WHERE extraction_id = ?
        ORDER BY id
    """, [extraction_id]).fetchall()
    
    doc_type = row.get("document_type", "Unknown")

    # Build response — common fields
    extraction: Dict[str, Any] = {
        "id": row["id"],
        "documentType": doc_type,
        "date": row["date"].isoformat() if row.get("date") else None,
        "summary": row.get("summary"),
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

    # Financial fields
    if doc_type in ("Invoice", "Receipt", "Bill", "Bank Statement", "Insurance EOB", "Unknown"):
        extraction.update({
            "vendorName": row.get("vendor_name"),
            "vendorAddress": row.get("vendor_address"),
            "invoiceNumber": row.get("invoice_number"),
            "dueDate": row["due_date"].isoformat() if row.get("due_date") else None,
            "totalAmount": float(row["total_amount"]) if row.get("total_amount") else 0.0,
            "taxAmount": float(row["tax_amount"]) if row.get("tax_amount") else 0.0,
            "currency": row.get("currency", "USD"),
            "accountNumber": row.get("account_number"),
            "billingPeriod": row.get("billing_period"),
        })

    # Research paper fields
    if doc_type == "Research Paper":
        extraction.update({
            "title": row.get("title"),
            "authors": json.loads(row["authors"]) if row.get("authors") else [],
            "abstract": row.get("abstract"),
            "journal": row.get("journal"),
            "doi": row.get("doi"),
            "publicationDate": row["publication_date"].isoformat() if row.get("publication_date") else None,
            "keywords": json.loads(row["keywords"]) if row.get("keywords") else [],
            "methodology": row.get("methodology"),
            "findings": row.get("findings"),
        })

    # Financial report fields
    if doc_type == "Financial Report":
        extraction.update({
            "companyName": row.get("company_name"),
            "reportType": row.get("report_type"),
            "reportPeriod": row.get("report_period"),
            "revenue": float(row["revenue"]) if row.get("revenue") else None,
            "expenses": float(row["expenses"]) if row.get("expenses") else None,
            "netIncome": float(row["net_income"]) if row.get("net_income") else None,
            "keyMetrics": json.loads(row["key_metrics"]) if row.get("key_metrics") else None,
        })
    
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
        conditions.append("(vendor_name ILIKE ? OR company_name ILIKE ? OR title ILIKE ?)")
        params.extend([f"%{vendor}%", f"%{vendor}%", f"%{vendor}%"])
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
               currency, date, created_at,
               title, company_name
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
            "vendorName": r[3] or r[8] or r[9] or "",  # vendor, title, or company
            "totalAmount": float(r[4]) if r[4] else 0.0,
            "currency": r[5],
            "date": r[6].isoformat() if r[6] else None,
            "createdAt": r[7].isoformat() if r[7] else None,
            "title": r[8],
            "companyName": r[9],
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
                e.tax_amount, e.summary, e.title, e.company_name,
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
                e.tax_amount, e.summary, e.title, e.company_name,
                l.description, l.quantity, l.unit_price, l.total, l.sku
            FROM extractions e
            LEFT JOIN line_items l ON e.id = l.extraction_id
            ORDER BY e.id, l.id
        """)
    
    # Convert to CSV
    csv_lines = []
    csv_lines.append("id,filename,document_type,vendor_name,total_amount,currency,date,invoice_number,tax_amount,summary,title,company_name,line_description,line_quantity,line_unit_price,line_total,line_sku")
    
    for row in result.fetchall():
        csv_line = ",".join([
            str(val).replace(",", ";") if val is not None else ""
            for val in row
        ])
        csv_lines.append(csv_line)
    
    return "\n".join(csv_lines).encode("utf-8")

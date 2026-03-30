import csv
import io
import os
import re
from PyPDF2 import PdfReader
from sqlalchemy import text
from text_to_sql.db_setup import get_engine


def sanitize_table_name(filename: str, customer_id: int) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
    name = re.sub(r'_+', '_', name).strip('_')
    return f"customer_{customer_id}_{name}"


def sanitize_column_name(col: str) -> str:
    col = re.sub(r'[^a-zA-Z0-9_]', '_', col).lower()
    col = re.sub(r'_+', '_', col).strip('_')
    return col or "column"


def process_csv(contents: bytes, filename: str, customer_id: int) -> str:
    engine = get_engine()
    table_name = sanitize_table_name(filename, customer_id)

    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)

    if not rows:
        raise ValueError("CSV file is empty")

    original_headers = reader.fieldnames
    sanitized_headers = []
    for h in original_headers:
        san = sanitize_column_name(h)
        # Rename columns that conflict with our auto-added columns
        if san in {"id", "customer_id"}:
            san = f"orig_{san}"
        sanitized_headers.append(san)

    # Build CREATE TABLE statement
    col_defs = ", ".join([f'"{col}" TEXT' for col in sanitized_headers])

    with engine.connect() as conn:
        # Drop if exists and recreate
        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
        conn.execute(text(
            f'CREATE TABLE "{table_name}" '
            f'(id SERIAL PRIMARY KEY, customer_id INTEGER, {col_defs})'
        ))
        conn.commit()

    # --- Fast bulk insert using psycopg2 COPY ---
    # Prepare CSV buffer with customer_id column prepended
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["customer_id"] + sanitized_headers)
    for row in rows:
        values = [customer_id]
        for orig in original_headers:
            values.append(row.get(orig, ""))
        writer.writerow(values)
    buffer.seek(0)

    # Get raw psycopg2 connection and use COPY FROM STDIN
    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        col_list = ', '.join(f'"{c}"' for c in ["customer_id"] + sanitized_headers)
        copy_sql = f'COPY "{table_name}" ({col_list}) FROM STDIN WITH CSV HEADER'
        cursor.copy_expert(copy_sql, buffer)
        raw_conn.commit()
    finally:
        raw_conn.close()

    # Register in uploaded_tables
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO uploaded_tables (customer_id, table_name, original_filename)
            VALUES (:customer_id, :table_name, :filename)
            ON CONFLICT DO NOTHING
        """), {"customer_id": customer_id, "table_name": table_name, "filename": filename})
        conn.commit()

    return table_name


def process_pdf(contents: bytes, filename: str, customer_id: int) -> int:
    reader = PdfReader(io.BytesIO(contents))
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() or ""

    return process_text_content(full_text, filename, customer_id)


def process_txt(contents: bytes, filename: str, customer_id: int) -> int:
    full_text = contents.decode("utf-8")
    return process_text_content(full_text, filename, customer_id)


def process_text_content(text_content: str, filename: str, customer_id: int) -> int:
    # Split into chunks of ~500 characters with overlap
    chunk_size = 500
    overlap = 50
    chunks = []

    text_content = text_content.strip()
    if not text_content:
        raise ValueError("No text content found in file")

    start = 0
    while start < len(text_content):
        end = start + chunk_size
        chunks.append(text_content[start:end])
        start = end - overlap

    # Embed and store each chunk
    from rag.embedder import embed_documents
    base_name = os.path.splitext(filename)[0]
    documents = [
        {
            "id": f"customer_{customer_id}_{base_name}_chunk_{i}",
            "text": chunk,
            "user_id": customer_id,  # rag_documents column is still named user_id
        }
        for i, chunk in enumerate(chunks)
    ]

    embed_documents(documents)
    return len(chunks)
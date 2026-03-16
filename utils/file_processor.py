import csv
import io
import os
import re
from PyPDF2 import PdfReader
from sqlalchemy import text
from text_to_sql.db_setup import get_engine


def sanitize_table_name(filename: str, user_id: int) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
    name = re.sub(r'_+', '_', name).strip('_')
    return f"user_{user_id}_{name}"


def sanitize_column_name(col: str) -> str:
    col = re.sub(r'[^a-zA-Z0-9_]', '_', col).lower()
    col = re.sub(r'_+', '_', col).strip('_')
    return col or "column"


def process_csv(contents: bytes, filename: str, user_id: int) -> str:
    engine = get_engine()
    table_name = sanitize_table_name(filename, user_id)

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
        if san in {"id", "user_id"}:
            san = f"orig_{san}"
        sanitized_headers.append(san)

    # Build CREATE TABLE statement
    col_defs = ", ".join([f'"{col}" TEXT' for col in sanitized_headers])

    with engine.connect() as conn:
        # Drop if exists and recreate
        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
        conn.execute(text(f'CREATE TABLE "{table_name}" (id SERIAL PRIMARY KEY, user_id INTEGER, {col_defs})'))

        # Insert rows in batches
        batch = []
        batch_size = 500

        for row in rows:
            new_row = {"user_id": user_id}
            for orig, san in zip(original_headers, sanitized_headers):
                new_row[san] = row.get(orig, "")
            batch.append(new_row)

            if len(batch) == batch_size:
                col_names = ", ".join([f'"{c}"' for c in ["user_id"] + sanitized_headers])
                placeholders = ", ".join([f":{c}" for c in ["user_id"] + sanitized_headers])
                conn.execute(text(f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'), batch)
                conn.commit()
                batch = []

        if batch:
            col_names = ", ".join([f'"{c}"' for c in ["user_id"] + sanitized_headers])
            placeholders = ", ".join([f":{c}" for c in ["user_id"] + sanitized_headers])
            conn.execute(text(f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'), batch)
            conn.commit()

        # Register in uploaded_tables
        conn.execute(text("""
            INSERT INTO uploaded_tables (user_id, table_name, original_filename)
            VALUES (:user_id, :table_name, :filename)
            ON CONFLICT DO NOTHING
        """), {"user_id": user_id, "table_name": table_name, "filename": filename})
        conn.commit()

    return table_name


def process_pdf(contents: bytes, filename: str, user_id: int) -> int:
    reader = PdfReader(io.BytesIO(contents))
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() or ""

    return process_text_content(full_text, filename, user_id)


def process_txt(contents: bytes, filename: str, user_id: int) -> int:
    full_text = contents.decode("utf-8")
    return process_text_content(full_text, filename, user_id)


def process_text_content(text_content: str, filename: str, user_id: int) -> int:
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
            "id": f"user_{user_id}_{base_name}_chunk_{i}",
            "text": chunk,
            "user_id": user_id
        }
        for i, chunk in enumerate(chunks)
    ]

    embed_documents(documents)
    return len(chunks)
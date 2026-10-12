import os
import sys
from sqlalchemy import text
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal

def test_db():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result]
        expected_tables = ["documents", "document_pages", "chunks"]
        for t in expected_tables:
            if t in tables:
                print(f"Table '{t}' exists.")
            else:
                print(f"Table '{t}' is MISSING.")
        
        ext_result = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        if ext_result.fetchone():
            print("pgvector extension is enabled.")
        else:
            print("pgvector extension is NOT enabled.")
    finally:
        db.close()

if __name__ == "__main__":
    test_db()

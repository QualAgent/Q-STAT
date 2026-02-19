# mcp/src/utils/db.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("POSTGRES_USER")
PASSWORD = os.getenv("POSTGRES_PASSWORD")
HOST = os.getenv("POSTGRES_HOST")
PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")

db_url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?sslmode=require"
engine = create_engine(db_url)


def execute_query(sql: str) -> dict:
    """SQL을 실행하고 결과를 반환"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))

            # SELECT 문인 경우
            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return {
                    "success": True,
                    "data": rows,
                    "columns": columns,
                    "row_count": len(rows),
                }
            else:
                return {"success": True, "affected_rows": result.rowcount}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_table_schemas() -> dict:
    """DB의 테이블/컬럼 정보를 조회 (text_to_sql에서 사용)"""
    sql = """
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """
    result = execute_query(sql)
    if not result["success"]:
        return {}

    schemas = {}
    for row in result["data"]:
        table = row["table_name"]
        if table not in schemas:
            schemas[table] = []
        schemas[table].append({
            "column": row["column_name"],
            "type": row["data_type"],
        })

    return schemas
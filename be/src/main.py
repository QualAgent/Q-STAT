from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
import importlib.metadata
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Q-STAT Agent API", version="0.1.0")

# CORS: Vue.js 프론트엔드에서의 API 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGINS", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/check/env")
def check_env():
    """환경변수 로드 상태 점검"""
    results = {}

    # LangGraph 설치 확인
    try:
        lg_version = importlib.metadata.version("langgraph")
        results["langgraph"] = {"status": "ok", "version": lg_version}
    except Exception as e:
        results["langgraph"] = {"status": "error", "detail": str(e)}

    # OpenAI API Key 확인
    if os.getenv("OPENAI_API_KEY"):
        results["openai_api_key"] = {"status": "ok"}
    else:
        results["openai_api_key"] = {"status": "missing"}

    return results


@app.get("/check/db")
def check_db():
    """Supabase PostgreSQL 연결 점검"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            sslmode="require",
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"status": "ok", "version": version}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

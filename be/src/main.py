from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
import importlib.metadata
import urllib.request
import json
from dotenv import load_dotenv

from src.routers.workflow import router as workflow_router

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


@app.get("/check/chromadb")
def check_chromadb():
    """ChromaDB 연결 점검"""
    try:
        url = "http://chromadb:8000/api/v2/heartbeat"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read())
        return {"status": "ok", "heartbeat": data}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/check/llm")
def check_llm():
    """LLM 연결 점검 (Ollama 또는 OpenAI)"""
    provider = os.getenv("LLM_PROVIDER", "ollama")
    try:
        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
            model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
            url = f"{base_url}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read())
            model_names = [m["name"] for m in data.get("models", [])]
            if any(model in name for name in model_names):
                return {"status": "ok", "provider": "ollama", "model": model}
            else:
                return {"status": "error", "provider": "ollama", "detail": f"'{model}' 모델 없음. 설치된 모델: {model_names}"}
        else:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key or api_key == "a123456789":
                return {"status": "error", "provider": "openai", "detail": "유효한 API Key 없음"}
            return {"status": "ok", "provider": "openai", "model": os.getenv("OPENAI_MODEL_ID", "gpt-4o")}
    except Exception as e:
        return {"status": "error", "provider": provider, "detail": str(e)}


# --- 라우터 등록 ---
app.include_router(workflow_router)

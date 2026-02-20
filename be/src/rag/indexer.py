"""
RAG 인덱서: knowledge/docs/ 아래 PDF를 ChromaDB에 적재.

실행 방법:
  docker compose exec be python -m src.rag.indexer

문서 성격별 청킹 전략:
  - REPORT           : chunk_size=400  (작은 단위로 검색)
  - MANUAL/SPEC/TECH_NOTE : chunk_size=800  (섹션 문맥 유지)
"""
import os
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.store import get_collection
from src.rag.embeddings import get_embeddings

load_dotenv()

KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", "/app/knowledge/docs"))


# ──────────────────────────────────────────
# doc_type 자동 분류 (파일명 키워드 기반)
# ──────────────────────────────────────────
def _detect_doc_type(filename: str) -> str:
    """파일명 키워드로 doc_type 자동 판별"""
    name = filename.lower()
    if any(k in name for k in ["이슈 대응 결과", "issue_report", "결과_esc", "결과_focus", "결과_shower"]):
        return "REPORT"
    if any(k in name for k in ["ocap", "대응 절차", "이슈 대응 절차"]):
        return "MANUAL"
    if any(k in name for k in ["tech_note", "tech note"]):
        return "TECH_NOTE"
    # 설비 구조, BOM, Hierarchy, Lifecycle → SPEC
    return "SPEC"


def _build_metadata(filename: str, doc_type: str) -> dict:
    """문서별 메타데이터 태깅"""
    meta = {
        "source": filename,
        "doc_type": doc_type,
        "equipment": "",
        "component": "",
    }
    return meta


# ──────────────────────────────────────────
# 청킹 전략
# ──────────────────────────────────────────
_SPLITTER_CONFIG = {
    "REPORT":    {"chunk_size": 400,  "chunk_overlap": 80},
    "MANUAL":    {"chunk_size": 800,  "chunk_overlap": 150},
    "SPEC":      {"chunk_size": 800,  "chunk_overlap": 150},
    "TECH_NOTE": {"chunk_size": 800,  "chunk_overlap": 150},
    "UNKNOWN":   {"chunk_size": 600,  "chunk_overlap": 100},
}


def _split(pages: list, doc_type: str) -> list:
    """페이지 리스트를 doc_type에 맞는 크기로 청킹"""
    cfg = _SPLITTER_CONFIG.get(doc_type, _SPLITTER_CONFIG["UNKNOWN"])
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg["chunk_size"],
        chunk_overlap=cfg["chunk_overlap"],
        separators=["\n\n", "\n", "。", ". ", " ", ""],
    )
    return splitter.split_documents(pages)


# ──────────────────────────────────────────
# ChromaDB 저장
# ──────────────────────────────────────────
def _upsert(chunks: list, base_metadata: dict, embeddings_model) -> int:
    """
    청크를 임베딩하여 ChromaDB에 upsert.
    doc_id = SHA256(source + chunk_index) — 재실행 시 중복 방지.
    """
    collection = get_collection()

    texts = [c.page_content for c in chunks]
    if not texts:
        return 0

    vectors = embeddings_model.embed_documents(texts)

    ids = []
    metadatas = []
    for i, chunk in enumerate(chunks):
        raw_id = f"{base_metadata['source']}_{i}"
        doc_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
        ids.append(doc_id)

        meta = {**base_metadata}
        # LangChain Document의 page 메타데이터 병합
        if chunk.metadata.get("page") is not None:
            meta["page"] = chunk.metadata["page"]
        metadatas.append(meta)

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=vectors,
        metadatas=metadatas,
    )
    return len(ids)


# ──────────────────────────────────────────
# 메인 진입점
# ──────────────────────────────────────────
def index_all_documents() -> None:
    """knowledge/docs/ 아래 모든 PDF를 ChromaDB에 적재"""
    pdf_files = list(KNOWLEDGE_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[indexer] PDF 없음: {KNOWLEDGE_DIR}")
        return

    embeddings = get_embeddings()
    total_chunks = 0

    for pdf_path in pdf_files:
        doc_type = _detect_doc_type(pdf_path.name)
        metadata = _build_metadata(pdf_path.name, doc_type)

        print(f"[indexer] 로드 중: {pdf_path.name} (doc_type={doc_type})")
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()

        chunks = _split(pages, doc_type)
        n = _upsert(chunks, metadata, embeddings)
        total_chunks += n

        print(f"  → {len(pages)} pages / {n} chunks 저장 완료")

    print(f"\n[indexer] 전체 완료: {len(pdf_files)}개 파일, {total_chunks}개 청크")


if __name__ == "__main__":
    index_all_documents()

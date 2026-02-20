"""
ChromaDB 연결 설정.

- 개발: ChromaDB HTTP 서버 (docker-compose의 chromadb 컨테이너)
- 컬렉션: "knowledge" (단일 컬렉션, doc_type 메타데이터로 구분)
"""
import os
import chromadb


def get_chroma_client() -> chromadb.HttpClient:
    """환경변수 기반 ChromaDB HTTP 클라이언트 반환"""
    host = os.getenv("CHROMADB_HOST", "chromadb")
    port = int(os.getenv("CHROMADB_PORT", "8000"))
    return chromadb.HttpClient(host=host, port=port)


def get_collection(name: str = "knowledge") -> chromadb.Collection:
    """
    지식 컬렉션 반환. 없으면 생성.

    메타데이터 스키마:
      - source:        파일명 (예: "Tech_Note_APC_Valve.pdf")
      - doc_type:      "MANUAL" | "REPORT" | "SPEC" | "TECH_NOTE"
      - equipment:     관련 장비 리스트 (문자열, 콤마 구분)
      - component:     관련 부품 리스트 (문자열, 콤마 구분)
      - incident_date: "YYYY-MM-DD" (REPORT인 경우만)
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )

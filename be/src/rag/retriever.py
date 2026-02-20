"""
RAG 검색기: Hybrid Search (BM25 + Vector + RRF 앙상블).

공유 사용처:
  - Column Selector Node (C 담당): 분석 후보 변수 추천
  - Action Advisor Node (D 담당): SOP/OCAP/이력 검색
  - QA Executor GENERAL_QA (Step 6): 일반 질의응답

동작 흐름:
  1. BM25  — ChromaDB에서 전체 문서 로드 후 키워드 빈도 기반 랭킹
  2. Vector — 쿼리 임베딩 후 ChromaDB cosine 유사도 랭킹
  3. RRF   — 두 랭킹을 Reciprocal Rank Fusion으로 통합
  4. top_k 결과 반환
"""
from __future__ import annotations

from rank_bm25 import BM25Okapi

from src.rag.store import get_collection
from src.rag.embeddings import get_embeddings


def search_knowledge(
    query: str,
    filter_dict: dict | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    하이브리드 검색 실행.

    Args:
        query:       검색 질의 (예: "APC Valve Drift", "O-ring fail symptom")
        filter_dict: ChromaDB where 절 필터
                     (예: {"doc_type": {"$in": ["MANUAL", "REPORT"]}})
        top_k:       반환할 최대 문서 수

    Returns:
        [
            {
                "doc_id":    str,
                "title":     str,    # source 파일명
                "relevance": float,  # 0.0 ~ 1.0 (RRF 정규화 점수)
                "content":   str,
                "metadata":  dict,
            },
            ...
        ]
    """
    collection = get_collection()

    bm25_hits = _bm25_search(query, collection, filter_dict, top_k * 2)
    vector_hits = _vector_search(query, collection, filter_dict, top_k * 2)
    fused = _rrf(bm25_hits, vector_hits)

    return fused[:top_k]


# ──────────────────────────────────────────
# BM25 검색
# ──────────────────────────────────────────
def _bm25_search(
    query: str,
    collection,
    filter_dict: dict | None,
    top_k: int,
) -> list[dict]:
    """
    ChromaDB에서 전체 문서(또는 필터된 문서)를 가져와 BM25 랭킹.
    부품번호, 장비명 등 정확 키워드 매칭에 강함.
    """
    where = filter_dict if filter_dict else None
    fetched = collection.get(
        where=where,
        include=["documents", "metadatas"],
    )

    docs = fetched["documents"]
    ids = fetched["ids"]
    metas = fetched["metadatas"]

    if not docs:
        return []

    # 한국어/영어 혼용 — 공백 기준 토크나이징 (기본)
    tokenized_corpus = [d.split() for d in docs]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query.split())

    ranked = sorted(
        zip(ids, docs, metas, scores),
        key=lambda x: x[3],
        reverse=True,
    )[:top_k]

    return [
        {
            "doc_id": doc_id,
            "title": meta.get("source", ""),
            "content": doc,
            "metadata": meta,
            "rank": rank + 1,
        }
        for rank, (doc_id, doc, meta, score) in enumerate(ranked)
        if score > 0
    ]


# ──────────────────────────────────────────
# Vector 검색
# ──────────────────────────────────────────
def _vector_search(
    query: str,
    collection,
    filter_dict: dict | None,
    top_k: int,
) -> list[dict]:
    """
    쿼리를 임베딩하여 ChromaDB cosine 유사도 기반 검색.
    증상 설명 등 의미 유사도 매칭에 강함.
    """
    embedding_model = get_embeddings()
    query_vector = embedding_model.embed_query(query)

    where = filter_dict if filter_dict else None
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]  # cosine distance (0=동일, 2=반대)

    return [
        {
            "doc_id": ids[i],
            "title": metas[i].get("source", ""),
            "content": docs[i],
            "metadata": metas[i],
            "rank": i + 1,
        }
        for i in range(len(ids))
    ]


# ──────────────────────────────────────────
# RRF 앙상블
# ──────────────────────────────────────────
def _rrf(
    bm25_results: list[dict],
    vector_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """
    Reciprocal Rank Fusion으로 두 랭킹 통합.
    score(d) = Σ 1 / (k + rank(d))

    k=60은 표준값 (Cormack et al., 2009).
    """
    scores: dict[str, float] = {}
    doc_store: dict[str, dict] = {}

    for rank, doc in enumerate(bm25_results):
        doc_id = doc["doc_id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (k + rank + 1)
        doc_store[doc_id] = doc

    for rank, doc in enumerate(vector_results):
        doc_id = doc["doc_id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (k + rank + 1)
        doc_store[doc_id] = doc

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    max_score = sorted_items[0][1] if sorted_items else 1.0

    return [
        {
            **doc_store[doc_id],
            "relevance": round(score / max_score, 4),
        }
        for doc_id, score in sorted_items
    ]

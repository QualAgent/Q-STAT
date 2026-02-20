"""
Action Advisor Node: 대응 제안기

해석된 원인에 대해 RAG 검색 기반으로
구체적인 조치 권고(Action Item)를 생성한다.

입력: state["interpretation"], state["problem"], state["execution"]
출력: state["recommendation"]
"""
from src.state_schemas.state import AnalysisState
from src.state_schemas.nodes import ActionRecommendation
from src.rag.retriever import search_knowledge
from src.llm import get_llm


def action_advisor_node(state: AnalysisState) -> AnalysisState:
    """
    Action Advisor Node 실행.

    CoT 동작 순서:
      1. interpretation.key_insights에서 원인 키워드 추출
      2. RAG 검색 — SOP, OCAP, 과거 Issue Report 조회
      3. 검색된 문서 컨텍스트 + LLM으로 조치 사항 생성
      4. 우선순위(immediate / preventive) 분류 후 action_plan 정렬
    """
    if state.get("interpretation") is None:
        raise ValueError("interpretation is missing")
    if state.get("problem") is None:
        raise ValueError("problem is missing")

    # TODO: Step 1 — key_insights에서 키워드 추출
    # keywords = _extract_keywords(state["interpretation"]["key_insights"])

    # TODO: Step 2 — RAG 검색
    # rag_results = []
    # for kw in keywords:
    #     rag_results += search_knowledge(kw, filter_dict={"doc_type": {"$in": ["MANUAL", "REPORT"]}})

    # TODO: Step 3 — LLM 조치 생성
    # llm = get_llm()
    # prompt = _build_advisor_prompt(state["interpretation"], rag_results)
    # response = llm.invoke(prompt)

    recommendation: ActionRecommendation = {
        "actions": [],      # {action_id, type, priority, description, steps, documents, expected_impact}
        "action_plan": [],  # action_id 순서 리스트 (priority 순)
    }

    return {**state, "recommendation": recommendation}


def _extract_keywords(insights: list[str]) -> list[str]:
    """key_insights 문장에서 검색용 핵심 키워드 추출"""
    # TODO: 구현
    return []


def _build_advisor_prompt(interpretation: dict, rag_docs: list[dict]) -> str:
    """LLM에게 전달할 조치 권고 프롬프트 생성"""
    # TODO: 구현
    return ""

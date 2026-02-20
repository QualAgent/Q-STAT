"""
Report Generator Node: 리포트 생성기

전체 분석 과정을 종합하여 최종 Markdown 리포트를 생성하고,
향후 '과거 사례'로 활용될 수 있도록 ChromaDB에 아카이빙한다.

입력: problem, columns, tools, execution, interpretation, recommendation (전부 필수)
출력: state["report"] (Markdown str)
"""
from src.state_schemas.state import AnalysisState
from src.llm import get_llm


_REQUIRED_FIELDS = [
    "problem",
    "columns",
    "tools",
    "execution",
    "interpretation",
    "recommendation",
]


def report_generator_node(state: AnalysisState) -> AnalysisState:
    """
    Report Generator Node 실행.

    동작 순서:
      1. 필수 필드 전부 존재 여부 확인
      2. 프론트엔드 합의 스키마(JSON)로 데이터 병합
      3. LLM이 Markdown 리포트 생성
      4. 생성된 리포트 요약을 ChromaDB에 아카이빙 (doc_type="REPORT")
    """
    for field in _REQUIRED_FIELDS:
        if state.get(field) is None:
            raise ValueError(f"{field} is missing")

    # TODO: Step 2 — JSON 병합 (프론트엔드 렌더링 스키마)
    # report_json = _build_report_json(state)

    # TODO: Step 3 — LLM Markdown 리포트 생성
    # llm = get_llm()
    # prompt = _build_report_prompt(state)
    # report_md = llm.invoke(prompt).content

    # TODO: Step 4 — ChromaDB 아카이빙
    # _archive_report(report_json)

    report: str = ""  # Markdown 문자열

    return {**state, "report": report}


def _build_report_json(state: AnalysisState) -> dict:
    """
    프론트엔드(Vue.js) 렌더링용 표준 JSON 구조 생성.

    {
        "report_id": "RPT-YYYYMMDD-NNN",
        "summary": str,
        "details": {
            "problem": ...,
            "columns": ...,
            "tools": ...,
            "execution": ...,
            "interpreter_result": ...,
            "action_plan": ...,
        },
        "evidence": [PDF 파일명 또는 doc_id 리스트],
    }
    """
    # TODO: 구현
    return {}


def _build_report_prompt(state: AnalysisState) -> str:
    """LLM에게 전달할 리포트 생성 프롬프트"""
    # TODO: 구현
    return ""


def _archive_report(report_json: dict) -> None:
    """
    생성된 리포트를 ChromaDB에 저장하여 향후 RAG 검색 대상으로 활용.
    doc_type = "REPORT"로 태깅.
    """
    # TODO: 구현 (src.rag.store.get_collection 사용)
    pass

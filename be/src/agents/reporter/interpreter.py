"""
Interpreter Node: 통계 결과 해석기

통계 에이전트의 Raw 수치를 자연어로 번역하고,
시각적 근거(그래프)를 생성한다.

입력: state["execution"], state["problem"]
출력: state["interpretation"]
"""
from src.state_schemas.state import AnalysisState
from src.state_schemas.nodes import InterpretationResults
from src.llm import get_llm


def interpreter_node(state: AnalysisState) -> AnalysisState:
    """
    Interpreter Node 실행.

    동작 순서:
      1. execution.results에서 유의미한 수치 필터링 (p < 0.05, r² > 0.8)
      2. LLM 호출 — "20년 차 공정 엔지니어" 역할로 통계 해석
      3. MCP plot_generator 호출 → 그래프 데이터 생성
      4. RE_ANALYSIS 모드(history[-1] 존재)인 경우 → Action Advisor 스킵 플래그 반환
    """
    if state.get("execution") is None:
        raise ValueError("execution is missing")
    if state.get("problem") is None:
        raise ValueError("problem is missing")

    # TODO: Step 1 — 유의미한 결과 필터링
    # significant = [
    #     r for r in state["execution"]["results"]
    #     if r["status"] == "success" and _is_significant(r["output"])
    # ]

    # TODO: Step 2 — LLM 통계 해석
    # llm = get_llm()
    # prompt = _build_interpretation_prompt(significant, state["problem"])
    # response = llm.invoke(prompt)

    # TODO: Step 3 — plot_generator 호출 (MCP)
    # chart_data = _call_plot_generator(significant)

    interpretation: InterpretationResults = {
        "interpretations": [],  # {execution_id, summary, explanation, chart_type, chart_data, significance}
        "key_insights": [],     # 핵심 인사이트 문장 리스트
    }

    return {**state, "interpretation": interpretation}


def _is_significant(output: dict) -> bool:
    """통계적으로 유의미한 결과인지 판단 (p < 0.05 or r² > 0.8)"""
    # TODO: 구현
    return True


def _build_interpretation_prompt(results: list, problem: dict) -> str:
    """LLM에게 전달할 해석 프롬프트 생성"""
    # TODO: 구현
    return ""

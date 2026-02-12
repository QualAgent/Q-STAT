from typing import TypedDict, List, Optional, Any, Dict, Annotated
import operator
from langchain_core.messages import BaseMessage
# 수정예정
# =============================================================================
# [1] 데이터 구조체 정의 (Sub-structures)
# =============================================================================

class IssueContext(TypedDict):
    """Data Monitor & Stat Analyzer가 공유하는 이슈 기본 정보"""
    issue_name: str         # 예: "Particle Contamination"
    target_line: str        # 예: "Line-A"
    target_equipment: str   # 예: "Etcher-01"
    timestamp: str          # 예: "2026-02-09T14:00:00"
    parameter: Optional[str]# 예: "CD" (Stat Analyzer가 분석 후 특정할 경우)

class SuspectItem(TypedDict):
    """Stat Analyzer가 도출한 원인 후보 항목"""
    rank: int               # 1, 2, 3...
    parameter: str          # 예: "o-ring", "Gas_Flow"
    analysis_method: str    # 예: "Z-score", "Trend Analysis"
    value: str              # 예: "8.4", "right-up"
    correlation_with_issue: float # 예: 0.92

class BomValidation(TypedDict):
    """Docs Researcher: 부품 수명 검증 결과"""
    part_name: str
    life_limit: float
    current_usage: float
    usage_ratio: float
    is_critical: bool

class HistoryCase(TypedDict):
    """Docs Researcher: 유사한 과거 사례 """
    case_id: str            # "PM_20250802"
    date: str
    similarity_score: float
    pm_type: str            # "Unscheduled"
    trigger_reason: str     # "Drift_Alarm"
    symptom_desc: str       # "Edge CD Drift"
    action_taken: str       # "Parts_Replace"
    replaced_part: Optional[str]
    action_detail: str
    result_status: str
    downtime_min: int

class HistoryStats(TypedDict):
    """Docs Researcher: 과거 사례 통계"""
    total_similar_cases: int
    success_count: int
    fail_count: int
    success_rate: float

class KnowledgeEvidence(TypedDict):
    """Docs Researcher의 최종 산출물"""
    bom_validation: Optional[BomValidation]
    history_match: Dict[str, Any] # 내부 키: found(bool), statistics(HistoryStats), top_case_info(HistoryCase)
    summary_text: str

# =============================================================================
# [2] 메인 에이전트 스테이트 (AgentState)
# =============================================================================

class AgentState(TypedDict):
    # --- 1. 기본 메타 데이터 ---
    lot_id: Optional[str]
    
    # LangGraph 필수: 대화 기록 누적용 (에러 로그나 중간 생각 저장)
    messages: Annotated[List[BaseMessage], operator.add]

    # --- 2. Data Monitor (지웅) Output ---
    raw_data: List[Dict[str, Any]]      # [{"timestamp":..., "pressure":...}, ...]
    
    # --- 3. Stat Analyzer (세연) Output ---
    issue_context: Optional[IssueContext] 
    suspect_rank: List[SuspectItem]     # 상위 5개 원인 목록
    is_analysis_complete: bool          # T -> Docs로 이동, F -> Data로 복귀 (재수집)
    
    # --- 4. Docs Researcher (현도) Output ---
    knowledge_evidence: Optional[KnowledgeEvidence]
    
    # --- 5. Strategy Advisor (도희) Output ---
    final_report: Optional[str]         # Markdown 형식의 최종 리포트 초안
    
    # --- 6. 흐름 제어용 ---
    next_step: Optional[str]            # 다음 실행할 노드 이름
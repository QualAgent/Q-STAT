"""LangGraph State 정의"""
from typing import TypedDict, Optional, List, Dict
from .nodes import (
    ProblemInfo,
    ColumnSelectionResult,
    ToolSelectionResult,
    ExecutionResults,
    InterpretationResults,
    ActionRecommendation
)

class AnalysisState(TypedDict):
    """
    전체 분석 State
    
    """
    
    trigger: Dict                                         # Monitor: 알람 정보
    problem: ProblemInfo                                  # Classify: 문제 정의
    columns: Optional[ColumnSelectionResult]              # Column Selector
    tools: Optional[ToolSelectionResult]                  # Tool Selection
    execution: Optional[ExecutionResults]                 # Executor
    interpretation: Optional[InterpretationResults]       # Interpreter
    recommendation: Optional[ActionRecommendation]        # Action Advisor
    
    # === 관리 ===
    history: List[Dict]         # 재분석 이력 (iteration별 snapshot)
    interactions: List[Dict]    # 사용자 대화 이력
    
    # === 최종 결과 ===
    report: Optional[str]       # Report Generator 출력
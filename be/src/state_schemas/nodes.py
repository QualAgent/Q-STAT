from typing import TypedDict, Optional, List, Dict
from datetime import datetime

# ==================== Classify Node ====================
class ProblemInfo(TypedDict):
    """문제 정의 (Classify Node 출력)"""
    problem_code: str
    description: str
    
    process_name: str
    equipment_id: str
    lot_number: str
    
    start_time: datetime
    end_time: datetime
    
    affected_parameter: str
    statistics: Dict  # min, max, avg, std
    severity: str

# ==================== Column Selector ====================
class ColumnSelectionResult(TypedDict):
    """선택된 컬럼 (Column Selector 출력)"""
    columns: List[Dict]  # column_name, reason, score
    strategy: str

# ==================== Tool Selection ====================
class ToolSelectionResult(TypedDict):
    """선택된 도구 (Tool Selection 출력)"""
    assignments: List[Dict]  # column_name, tool_name, etc

# ==================== Executor ====================
class ExecutionResults(TypedDict):
    """분석 실행 결과 (Executor 출력)"""
    results: List[Dict]  # tool_name, output, status
    summary: Dict  # total, success, failed

# ==================== Interpreter ====================
class InterpretationResults(TypedDict):
    """결과 해석 (Interpreter 출력)"""
    interpretations: List[Dict]  # summary, explanation, chart
    key_insights: List[str]

# ==================== Action Advisor ====================
class ActionRecommendation(TypedDict):
    """조치 권고 (Action Advisor 출력)"""
    actions: List[Dict]  # action, priority, steps, documents
    action_plan: List[str]
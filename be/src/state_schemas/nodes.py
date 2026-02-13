"""
각 노드의 입출력 타입 정의
"""
from typing import TypedDict, Optional, List, Dict, Tuple
from datetime import datetime

# ==================== Monitor Node ====================
class SPCViolation(TypedDict):
    """Monitor Node 출력"""
    rule_type: str
    rule_description: str
    violated_points: List[Tuple[datetime, float]]
    control_limits: Dict[str, float]
    sigma_level: float
    consecutive_violation: bool


# ==================== Classify Node ====================
class ProblemInfo(TypedDict):
    """Classify Node 출력"""
    problem_code: str
    problem_category: str
    description: str
    
    process_name: str
    equipment_id: str
    lot_number: str
    
    detection_time: datetime
    problem_start_time: datetime
    problem_end_time: datetime
    affected_duration: float
    
    affected_parameter: str
    representative_values: Dict[str, float]
    sample_size: int
    
    severity_level: str


# ==================== Column Selector Node ====================
class ColumnSelectionResult(TypedDict):
    """Column Selector Node 출력"""
    selected_columns: List[Dict]  # column_name, selection_reason, relevance_score
    rejected_columns: List[Dict]
    selection_strategy: str


# ==================== Tool Selection Node ====================
class ToolSelectionResult(TypedDict):
    """Tool Selection Node 출력"""
    tool_assignments: List[Dict]  # column_name, tool_name, rationale
    available_tools: List[str]


# ==================== Executor Node ====================
class ExecutionResults(TypedDict):
    """Executor Node 출력"""
    results: List[Dict]  # execution_id, tool_name, statistical_output, status
    execution_summary: Dict


# ==================== Interpreter Node ====================
class InterpretationResults(TypedDict):
    """Interpreter Node 출력"""
    interpretations: List[Dict]  # summary, explanation, chart_data
    integrated_summary: str
    key_insights: List[str]


# ==================== Action Advisor Node ====================
class ActionRecommendation(TypedDict):
    """Action Advisor Node 출력"""
    recommendations: List[Dict]  # action, priority, steps, documents
    prioritized_action_plan: List[str]
    related_cases: List[Dict]  # 과거 유사 사례
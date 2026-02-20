from pydantic import BaseModel
from typing import List, Literal, Optional


class AnalysisItem(BaseModel):
    analysis_id: str
    problem_code: str
    detection_time: str  # ISO 8601
    process_name: str
    equipment_id: str
    severity: Literal["low", "medium", "high"]
    status: Literal["completed", "failed", "running"]
    completed_at: Optional[str] = None  # ISO 8601 or None


class AnalysisListData(BaseModel):
    analysis: List[AnalysisItem]
    total: int


class AnalysisProblem(BaseModel):
    problem_code: str
    description: str
    severity: Literal["low", "medium", "high"]


class AnalysisRecommendation(BaseModel):
    priority: Literal["low", "medium", "high"]
    action: str


class AnalysisDetailData(BaseModel):
    analysis_id: str
    problem: AnalysisProblem
    key_findings: List[str]
    recommendations: List[AnalysisRecommendation]
    report_url: str
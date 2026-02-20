from pydantic import BaseModel
from typing import List


# ===== Request =====

class TriggerInfo(BaseModel):
    rule_type: str
    detection_time: str
    severity: str


class ProblemInfo(BaseModel):
    problem_code: str
    process_name: str
    equipment_id: str


class SPCViolationRequest(BaseModel):
    trigger: TriggerInfo
    problem: ProblemInfo


class ReportCompleteRequest(BaseModel):
    analysis_id: str
    problem_code: str
    report_url: str


# ===== Response Data =====

class NotificationResult(BaseModel):
    notification_sent: bool
    channels: List[str]
    recipients: List[str] | None = None
    report_url: str | None = None

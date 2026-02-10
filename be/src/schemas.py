from pydantic import BaseModel
from datetime import datetime


# --- 사용자가 프론트에서 분석 요청할 때 ---
class TaskRequest(BaseModel):
    user_input: str                    # "가스랑 PM 둘 다 p-value 구해봐"
    eqp_id: str | None = None         # 특정 장비 지정 (선택)
    lot_id: str | None = None         # 특정 Lot 지정 (선택)


# --- 스케줄러가 drift 감지했을 때 ---
class DriftAlert(BaseModel):
    metric: str                        # "cd_value"
    eqp_id: str                        # "ETCHER_01"
    drift_pct: float                   # 0.2 (0.2% 상승)
    time_from: datetime                # drift 시작 시점
    time_to: datetime                  # 감지 시점
    summary: str                       # "Edge CD 값의 비정상적 Drift 발생"


# --- 최종 결과를 프론트에 반환할 때 ---
class TaskResponse(BaseModel):
    task_id: str                       # 추적용 ID
    status: str                        # "completed" / "failed"
    summary: str                       # 분석 요약
    root_cause: str | None = None      # 추정 원인
    recommended_action: str | None = None  # 권장 조치
    created_at: datetime

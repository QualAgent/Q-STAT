from fastapi import APIRouter
from datetime import datetime
import uuid

from src.schemas import TaskRequest, DriftAlert, TaskResponse

router = APIRouter()


@router.post("/run-workflow", response_model=TaskResponse)
async def run_workflow(request: TaskRequest):
    task_id = str(uuid.uuid4())

    # TODO: Orchestrator 에이전트 호출
    # result = orchestrator.invoke({"user_input": request.user_input, ...})

    return TaskResponse(
        task_id=task_id,
        status="completed",
        summary=f"[더미 응답] 입력: {request.user_input}",
        root_cause=None,
        recommended_action=None,
        created_at=datetime.now(),
    )


@router.post("/drift-alert", response_model=TaskResponse)
async def handle_drift(alert: DriftAlert):
    task_id = str(uuid.uuid4())

    # TODO: Orchestrator 에이전트 호출
    # result = orchestrator.invoke({"drift_summary": alert.summary, ...})

    return TaskResponse(
        task_id=task_id,
        status="completed",
        summary=f"[더미 응답] Drift 감지: {alert.summary}",
        root_cause=None,
        recommended_action=None,
        created_at=datetime.now(),
    )

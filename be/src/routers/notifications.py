from fastapi import APIRouter
from src.schemas.notifications import (
    SPCViolationRequest,
    ReportCompleteRequest,
    NotificationResult,
)
from src.schemas.common import success, error

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/spc-violation")
def spc_violation(payload: SPCViolationRequest):
    """
    Monitor 감지 이상 알림
    """

    try:
        # TODO: 실제 알림 발송 로직 추가 (services/~)
        result = NotificationResult(
            notification_sent=True,
            channels=["email", "frontend"],
            recipients=["engineer@company.com"],
        )

        return success(
            "SPC 위반 알림이 발송되었습니다",
            data=result.model_dump(),
            code=201,
        )

    except Exception as e:
        return error(
            "이메일 발송에 실패했습니다",
            data={"detail": str(e)},
            code=500,
        )


@router.post("/report-complete")
def report_complete(payload: ReportCompleteRequest):
    """
    리포트 완료 알림
    """

    try:
        # TODO: 실제 알림 발송 로직 추가 (services/~)
        result = NotificationResult(
            notification_sent=True,
            channels=["email", "frontend"],
            report_url=payload.report_url,
        )

        return success(
            "리포트 완료 알림이 발송되었습니다",
            data=result.model_dump(),
            code=201,
        )

    except Exception as e:
        return error(
            "리포트 알림 발송 중 오류가 발생했습니다",
            data={"detail": str(e)},
            code=500,
        )

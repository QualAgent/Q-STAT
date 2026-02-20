from fastapi import APIRouter, Query
from typing import Literal

from src.schemas.common import success, fail, error
from src.schemas.dashboard import (
    AnalysisListData,
    AnalysisItem,
    AnalysisDetailData,
    AnalysisProblem,
    AnalysisRecommendation,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/analysis")
def list_analysis(
    limit: int = Query(20, ge=1, le=200),
    status: Literal["all", "completed", "failed", "running"] = Query("all"),
):
    """
    분석 이력 목록 조회
    GET /dashboard/analysis
    """
    try:
        # TODO: DB 조회로 교체 (services/~)
        items = [
            AnalysisItem(
                analysis_id="analysis_20240219_001",
                problem_code="SPC-001-UCL",
                detection_time="2024-02-19T10:15:30Z",
                process_name="Etching",
                equipment_id="EQP-001",
                severity="high",
                status="completed",
                completed_at="2024-02-19T10:35:00Z",
            )
        ]

        # TODO: 실제 DB 조회하게 되면 SQL문의 WHERE 조건으로 대체 예정
        if status != "all":
            items = [x for x in items if x.status == status]

        data = AnalysisListData(analysis=items[:limit], total=len(items))

        return success("분석 목록을 조회했습니다", data=data.model_dump(), code=200)

    except Exception as e:
        return error("데이터베이스 조회 중 오류가 발생했습니다", data={"detail": str(e)}, code=500)


@router.get("/analysis/{id}")
def get_analysis_detail(id: str):
    """
    분석 결과 상세 조회
    GET /dashboard/analysis/{id}
    """
    try:
        # TODO: DB 조회로 교체 
        if id != "analysis_20240219_001":
            return fail("분석 결과를 찾을 수 없습니다", data={"analysis_id": id}, code=404)

        data = AnalysisDetailData(
            analysis_id=id,
            problem=AnalysisProblem(
                problem_code="SPC-001-UCL",
                description="Control limit violation on CD_uniformity",
                severity="high",
            ),
            key_findings=["Gas flow rate increased by 10%"],
            recommendations=[
                AnalysisRecommendation(priority="high", action="Adjust gas flow rate to 150 sccm")
            ],
            report_url=f"/reports/{id}",
        )

        return success("분석 상세 정보를 조회했습니다", data=data.model_dump(), code=200)

    except Exception as e:
        return error("분석 상세 조회 중 오류가 발생했습니다", data={"detail": str(e)}, code=500)
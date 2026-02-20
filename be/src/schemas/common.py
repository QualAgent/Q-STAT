from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    ERROR = "ERROR"


def utc_now_iso() -> str:
    """표준 응답 timestamp 생성 (ISO 8601, UTC, Z suffix)"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ApiResponse(BaseModel, Generic[T]):
    '''api 표준 응답 구조'''
    status: ApiStatus
    code: str = Field(..., description="HTTP 상태 코드")
    message: str = Field(..., description="응답 메시지 (한글)")
    data: Optional[T] = Field(default=None, description="실제 데이터 (실패 시 null)")
    timestamp: str = Field(default_factory=utc_now_iso, description="응답 시각 (ISO 8601)")


def success(message: str, data: Optional[T] = None, code: int = 200) -> ApiResponse[T]:
    return ApiResponse(status=ApiStatus.SUCCESS, code=str(code), message=message, data=data)


def fail(message: str, data: Optional[T] = None, code: int = 400) -> ApiResponse[T]:
    return ApiResponse(status=ApiStatus.FAIL, code=str(code), message=message, data=data)


def error(message: str, data: Optional[T] = None, code: int = 500) -> ApiResponse[T]:
    return ApiResponse(status=ApiStatus.ERROR, code=str(code), message=message, data=data)

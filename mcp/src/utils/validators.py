# mcp/src/utils/validators.py
import numpy as np
import pandas as pd


def validate_data(data: list[dict], required_columns: list[str]) -> tuple[bool, str, pd.DataFrame | None]:
    """
    입력 데이터를 검증하고 DataFrame으로 변환

    Returns:
        (is_valid, error_message, dataframe)
    """
    if not data:
        return False, "데이터가 비어 있습니다.", None

    df = pd.DataFrame(data)

    # 필수 컬럼 존재 확인
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return False, f"누락된 컬럼: {missing}. 사용 가능한 컬럼: {list(df.columns)}", None

    return True, "", df


def validate_numeric_columns(df: pd.DataFrame, columns: list[str]) -> tuple[bool, str]:
    """숫자형 컬럼인지 검증"""
    for col in columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            # 숫자 변환 시도
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                null_count = df[col].isna().sum()
                if null_count > len(df) * 0.5:
                    return False, f"'{col}' 컬럼의 50% 이상이 숫자로 변환 불가"
            except Exception:
                return False, f"'{col}' 컬럼이 숫자형이 아닙니다."

    return True, ""


def clean_numeric_data(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """숫자형 컬럼의 NaN 제거 후 반환"""
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=columns)
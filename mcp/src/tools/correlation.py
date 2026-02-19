# mcp/src/tools/correlation.py
import time
import numpy as np
from scipy import stats
from src.utils.validators import validate_data, validate_numeric_columns, clean_numeric_data


async def correlation_analysis(
    target: str,
    features: list[str],
    data: list[dict],
    options: dict | None = None,
) -> dict:
    """
    target 변수와 각 feature 간의 상관계수 및 p-value를 계산합니다.

    Args:
        target: 종속변수 컬럼명 (ex. "cd_value")
        features: 독립변수 컬럼명 목록 (ex. ["pressure", "temp_chuck", "gas_flow_total"])
        data: 분석 대상 데이터
        options: {"method": "pearson" | "spearman" | "kendall"}

    Returns:
        각 feature별 상관계수(r), p-value, 유의성 판정
    """
    start = time.time()
    method = (options or {}).get("method", "pearson")

    all_columns = [target] + features
    is_valid, error, df = validate_data(data, all_columns)
    if not is_valid:
        return {"tool_name": "correlation_analysis", "error": error, "execution_time_ms": 0}

    is_numeric, error = validate_numeric_columns(df, all_columns)
    if not is_numeric:
        return {"tool_name": "correlation_analysis", "error": error, "execution_time_ms": 0}

    df = clean_numeric_data(df, all_columns)

    if len(df) < 3:
        return {"tool_name": "correlation_analysis", "error": "유효 데이터 3건 미만", "execution_time_ms": 0}

    results = {}
    target_values = df[target].values

    for feat in features:
        feat_values = df[feat].values

        try:
            if method == "pearson":
                r, p = stats.pearsonr(target_values, feat_values)
            elif method == "spearman":
                r, p = stats.spearmanr(target_values, feat_values)
            elif method == "kendall":
                r, p = stats.kendalltau(target_values, feat_values)
            else:
                r, p = stats.pearsonr(target_values, feat_values)

            results[feat] = {
                "r": round(float(r), 4),
                "p_value": round(float(p), 6),
                "is_significant": p < 0.05,
                "strength": _classify_correlation(abs(r)),
            }
        except Exception as e:
            results[feat] = {"error": str(e)}

    elapsed = int((time.time() - start) * 1000)
    return {
        "tool_name": "correlation_analysis",
        "results": results,
        "method": method,
        "sample_size": len(df),
        "execution_time_ms": elapsed,
    }


def _classify_correlation(abs_r: float) -> str:
    if abs_r >= 0.8:
        return "strong"
    elif abs_r >= 0.5:
        return "moderate"
    elif abs_r >= 0.3:
        return "weak"
    else:
        return "negligible"
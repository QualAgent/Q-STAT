
import time
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf
from src.utils.validators import validate_data

async def time_series_analysis(
    target: str,
    features: list[str], # [timestamp_column]
    data: list[dict],
    options: dict | None = None,
) -> dict:
    """
    시계열 분석을 수행합니다. (추세, 계절성 분해, 자기상관)
    
    Args:
        target: 분석할 수치형 시계열 데이터 컬럼
        features: [시간 컬럼]
        options: {"period": int (계절성 주기), "model": "additive"|"multiplicative"}
    """
    start = time.time()
    options = options or {}
    period = options.get("period", None)
    model = options.get("model", "additive")
    
    if not features:
        return {"tool_name": "time_series_analysis", "error": "Timestamp column required in features", "execution_time_ms": 0}
        
    time_col = features[0]
    
    is_valid, error, df = validate_data(data, [target, time_col])
    if not is_valid:
        return {"tool_name": "time_series_analysis", "error": error, "execution_time_ms": 0}
    
    try:
        # 시간 컬럼 변환 및 정렬
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.sort_values(by=time_col)
        df = df.set_index(time_col)
        
        # 숫자형 변환 및 결측치 처리
        series = pd.to_numeric(df[target], errors='coerce').interpolate(method='linear').dropna()
        
        results = {}
        
        # 1. 기본 통계 및 이동평균
        results["summary"] = series.describe().to_dict()
        results["moving_average_5"] = series.rolling(window=5).mean().fillna(0).tolist() # 간단한 MA
        
        # 2. 자기상관 (ACF)
        # nlags는 데이터 길이에 따라 조정
        nlags = min(40, len(series) // 2)
        acf_values = acf(series, nlags=nlags, fft=True)
        results["autocorrelation"] = acf_values.tolist()
        
        # 3. 시계열 분해 (Decomposition)
        # period가 없으면 데이터 빈도로 추론 시도하거나 에러
        if period is None:
             # 간단히 인덱스 빈도 확인 시도
             if series.index.inferred_freq:
                 pass # statsmodels가 알아서 함
             else:
                 # 임의 설정 (데이터가 충분하다면)
                 if len(series) > 14: period = 7 # 일주일 가정
                 
        if period and len(series) >= 2 * period:
            decomposition = seasonal_decompose(series, model=model, period=period)
            results["decomposition"] = {
                "trend": decomposition.trend.fillna(0).tolist(),
                "seasonal": decomposition.seasonal.fillna(0).tolist(),
                # "resid": decomposition.resid.fillna(0).tolist()
            }
        else:
            results["decomposition_note"] = "Not enough data or period unspecified for decomposition"

    except Exception as e:
        return {"tool_name": "time_series_analysis", "error": str(e), "execution_time_ms": int((time.time() - start) * 1000)}

    return {
        "tool_name": "time_series_analysis",
        "results": results,
        "execution_time_ms": int((time.time() - start) * 1000)
    }

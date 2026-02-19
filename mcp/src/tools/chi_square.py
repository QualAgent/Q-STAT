
import time
import pandas as pd
import numpy as np
from scipy import stats
from src.utils.validators import validate_data

async def chi_square_test(
    target: str,
    features: list[str],
    data: list[dict],
    options: dict | None = None,
) -> dict:
    """
    카이제곱 독립성 검정 (Chi-Square Test for Independence)을 수행합니다.
    
    Args:
        target: 첫 번째 범주형 변수
        features: [두 번째 범주형 변수]
        data: 데이터 리스트
    """
    start = time.time()
    
    if not features:
        return {"tool_name": "chi_square_test", "error": "Features list required (2nd categorical variable)", "execution_time_ms": 0}
        
    var1 = target
    var2 = features[0]
    
    is_valid, error, df = validate_data(data, [var1, var2])
    if not is_valid:
        return {"tool_name": "chi_square_test", "error": error, "execution_time_ms": 0}
    
    df = df.dropna()
    
    try:
        # 교차표 생성
        contingency_table = pd.crosstab(df[var1], df[var2])
        
        # 카이제곱 검정
        chi2, p, dof, expected = stats.chi2_contingency(contingency_table)
        
        # 결과 정리
        results = {
            "chi2_statistic": float(chi2),
            "p_value": float(p),
            "degrees_of_freedom": int(dof),
            "contingency_table": contingency_table.to_dict(),
            "expected_frequencies": expected.tolist()
        }
        
    except Exception as e:
        return {"tool_name": "chi_square_test", "error": str(e), "execution_time_ms": int((time.time() - start) * 1000)}

    return {
        "tool_name": "chi_square_test",
        "results": results,
        "execution_time_ms": int((time.time() - start) * 1000)
    }

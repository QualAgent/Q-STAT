
import time
import numpy as np
import pandas as pd
from scipy import stats
from src.utils.validators import validate_data

def calculate_cohens_d(group1, group2):
    """Calculate Cohen's d for effect size."""
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled Standard Deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    return (np.mean(group1) - np.mean(group2)) / pooled_std if pooled_std != 0 else 0

async def t_test(
    target: str,
    features: list[str],
    data: list[dict],
    options: dict | None = None,
) -> dict:
    """
    T-Test를 수행합니다 (Independent or Paired).
    
    Args:
        target: 종속변수 (수치형)
        features: 
            - Independent: [그룹변수] (2개의 고유값 필요)
            - Paired: [두번째 수치변수] (target vs feature[0])
        data: 데이터 리스트
        options: {"paired": bool, "equal_var": bool}
    """
    start = time.time()
    options = options or {}
    is_paired = options.get("paired", False)
    equal_var = options.get("equal_var", True)
    
    # 데이터 검증
    required_cols = [target] + features
    is_valid, error, df = validate_data(data, required_cols)
    if not is_valid:
        return {"tool_name": "t_test", "error": error, "execution_time_ms": 0}
        
    df = df.dropna()

    result_stats = {}
    

    try:
        col_target = df[target]
        col_feature = df[features[0]]

        # Feature 컬럼이 수치형인지 확인
        try:
            col_feature_numeric = pd.to_numeric(col_feature, errors='raise')
            is_feature_numeric = True
        except ValueError:
            is_feature_numeric = False

        # --- CASE 1: 두 수치형 컬럼 비교 (Wide Format) ---
        if is_feature_numeric:
            group1 = pd.to_numeric(col_target, errors='coerce').dropna()
            group2 = col_feature_numeric.dropna()

            # 데이터 정렬 (인덱스 기준 교집합)
            common_idx = group1.index.intersection(group2.index)
            group1 = group1.loc[common_idx]
            group2 = group2.loc[common_idx]

            if len(group1) < 2 or len(group2) < 2:
                return {"tool_name": "t_test", "error": "Not enough data", "execution_time_ms": 0}

            if is_paired:
                # Paired T-test
                t_stat, p_val = stats.ttest_rel(group1, group2)
                d = calculate_cohens_d(group1, group2)
                test_type = "paired_two_columns"
            else:
                # Independent T-test (Two variable columns)
                t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=equal_var)
                d = calculate_cohens_d(group1, group2)
                test_type = "independent_two_columns"

            result_stats = {
                "type": test_type,
                "t_statistic": float(t_stat),
                "p_value": float(p_val),
                "effect_size_cohens_d": float(d),
                "stats": {
                    target: {"mean": float(group1.mean()), "count": int(len(group1))},
                    features[0]: {"mean": float(group2.mean()), "count": int(len(group2))}
                }
            }

        # --- CASE 2: 그룹별 비교 (Long Format) ---
        else:
            # Categorical Feature -> Grouping Variable
            if is_paired:
                 return {
                    "tool_name": "t_test", 
                    "error": "Paired t-test requires two numeric columns (not numeric vs categorical group).", 
                    "execution_time_ms": 0
                }

            # Grouping Logic
            groups = col_feature.unique()
            if len(groups) != 2:
                return {
                    "tool_name": "t_test",
                    "error": f"Independent t-test by group requires exactly 2 unique groups, found {len(groups)}: {groups}",
                    "execution_time_ms": 0
                }
            
            group1_val = groups[0]
            group2_val = groups[1]
            
            group1_data = pd.to_numeric(df[df[features[0]] == group1_val][target], errors='coerce').dropna()
            group2_data = pd.to_numeric(df[df[features[0]] == group2_val][target], errors='coerce').dropna()
            
            if len(group1_data) < 2 or len(group2_data) < 2:
                return {"tool_name": "t_test", "error": "Not enough data in groups", "execution_time_ms": 0}

            t_stat, p_val = stats.ttest_ind(group1_data, group2_data, equal_var=equal_var)
            d = calculate_cohens_d(group1_data, group2_data)
            
            result_stats = {
                "type": "independent_grouped",
                "groups": [str(group1_val), str(group2_val)],
                "t_statistic": float(t_stat),
                "p_value": float(p_val),
                "effect_size_cohens_d": float(d),
                "stats": {
                    str(group1_val): {"mean": float(group1_data.mean()), "count": int(len(group1_data))},
                    str(group2_val): {"mean": float(group2_data.mean()), "count": int(len(group2_data))}
                }
            }

    except Exception as e:
        return {"tool_name": "t_test", "error": str(e), "execution_time_ms": int((time.time() - start) * 1000)}

    return {
        "tool_name": "t_test",
        "results": result_stats,
        "execution_time_ms": int((time.time() - start) * 1000)
    }

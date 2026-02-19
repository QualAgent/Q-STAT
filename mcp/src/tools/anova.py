import time
import pandas as pd
from scipy import stats
from src.utils.validators import validate_data

async def anova_test(
    target: str,
    features: list[str],
    data: list[dict],
    options: dict | None = None,
) -> dict:
    """
    일원분산분석(One-way ANOVA)을 수행합니다.
    Target은 수치형, Features는 범주형(그룹) 변수여야 합니다.

    Args:
        target: 종속변수 (수치형)
        features: 그룹 변수 목록 (범주형)
        data: 분석할 데이터 리스트
        options: 예비 (현재 사용 안함)
    """
    start = time.time()

    # 1. 데이터 검증 (Target + Features 컬럼 존재 여부)
    all_columns = [target] + features
    is_valid, error, df = validate_data(data, all_columns)
    if not is_valid:
        return {
            "tool_name": "anova_test",
            "error": error,
            "execution_time_ms": int((time.time() - start) * 1000)
        }

    # 2. Target 수치형 변환 및 결측치 제거
    # Features(그룹)는 문자열일 수 있으므로 수치 변환 강제하지 않음
    try:
        df[target] = pd.to_numeric(df[target], errors='coerce')
    except Exception:
        return {
            "tool_name": "anova_test",
            "error": f"Target '{target}' column conversion to numeric failed",
            "execution_time_ms": int((time.time() - start) * 1000)
        }

    # Target NaN 제거
    df = df.dropna(subset=[target])
    
    if df.empty:
        return {
            "tool_name": "anova_test",
            "error": "No valid data after cleaning target column",
            "execution_time_ms": int((time.time() - start) * 1000)
        }

    results = {}

    # 3. 각 Feature(그룹)별 ANOVA 수행
    for group_col in features:
        # 해당 그룹 컬럼의 결측치 제거
        sub_df = df.dropna(subset=[group_col])
        
        # 그룹별 데이터 수집
        groups = sub_df.groupby(group_col)[target].apply(list)

        # 그룹이 2개 미만이면 ANOVA 의미 없음
        if len(groups) < 2:
            results[group_col] = {
                "error": f"Not enough groups (found {len(groups)}) for feature '{group_col}'"
            }
            continue
        
        # Scipy 입력 준비 (각 그룹의 값 리스트)
        # 데이터가 너무 적은(1개 이하) 그룹은 제외하거나 포함할지 결정 필요.
        # f_oneway는 샘플이 필요함.
        group_values = [v for v in groups.values if len(v) > 0]
        
        if len(group_values) < 2:
             results[group_col] = {
                "error": f"Not enough valid groups with data for '{group_col}'"
            }
             continue

        try:
            # ANOVA 실행
            f_stat, p_val = stats.f_oneway(*group_values)
            
            # 그룹별 통계 (Mean, Std, Count)
            stats_df = sub_df.groupby(group_col)[target].agg(['mean', 'std', 'count'])
            
            group_stats = {}
            for idx, row in stats_df.iterrows():
                group_stats[str(idx)] = {
                    "mean": round(row['mean'], 4),
                    "std": round(row['std'], 4) if pd.notna(row['std']) else 0.0,
                    "count": int(row['count'])
                }

            results[group_col] = {
                "f_statistic": round(float(f_stat), 4),
                "p_value": round(float(p_val), 6),
                "is_significant": float(p_val) < 0.05,
                "group_stats": group_stats
            }

        except Exception as e:
            results[group_col] = {"error": str(e)}

    elapsed = int((time.time() - start) * 1000)
    
    return {
        "tool_name": "anova_test",
        "results": results,
        "execution_time_ms": elapsed
    }

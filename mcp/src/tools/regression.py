# mcp/src/tools/regression.py
import time
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from src.utils.validators import validate_data, validate_numeric_columns, clean_numeric_data


async def regression_analysis(
    target: str,
    features: list[str],
    data: list[dict],
    options: dict | None = None,
) -> dict:
    """
    다중 선형 회귀분석을 수행합니다.

    Returns:
        R-squared, 각 feature별 계수(coefficient), p-value, VIF 등
    """
    start = time.time()

    all_columns = [target] + features
    is_valid, error, df = validate_data(data, all_columns)
    if not is_valid:
        return {"tool_name": "regression_analysis", "error": error, "execution_time_ms": 0}

    is_numeric, error = validate_numeric_columns(df, all_columns)
    if not is_numeric:
        return {"tool_name": "regression_analysis", "error": error, "execution_time_ms": 0}

    df = clean_numeric_data(df, all_columns)

    if len(df) < len(features) + 2:
        return {"tool_name": "regression_analysis", "error": "데이터 수가 변수 수보다 적음", "execution_time_ms": 0}

    X = df[features].values
    y = df[target].values

    # sklearn 회귀
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    # R-squared
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    # 각 계수의 p-value 계산
    n = len(y)
    p = len(features)
    dof = n - p - 1

    if dof > 0:
        mse = ss_res / dof
        X_with_intercept = np.column_stack([np.ones(n), X])
        try:
            var_beta = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept).diagonal()
            se = np.sqrt(np.abs(var_beta))
            t_stats = np.append(model.intercept_, model.coef_) / se
            p_values = [float(2 * (1 - stats.t.cdf(abs(t), dof))) for t in t_stats]
        except np.linalg.LinAlgError:
            p_values = [None] * (p + 1)
    else:
        p_values = [None] * (p + 1)

    # 결과 구성
    coefficients = {}
    for i, feat in enumerate(features):
        coefficients[feat] = {
            "coefficient": round(float(model.coef_[i]), 6),
            "p_value": round(p_values[i + 1], 6) if p_values[i + 1] is not None else None,
            "is_significant": p_values[i + 1] < 0.05 if p_values[i + 1] is not None else None,
        }

    elapsed = int((time.time() - start) * 1000)
    return {
        "tool_name": "regression_analysis",
        "results": {
            "r_squared": round(float(r_squared), 4),
            "adjusted_r_squared": round(float(1 - (1 - r_squared) * (n - 1) / dof), 4) if dof > 0 else None,
            "intercept": round(float(model.intercept_), 6),
            "coefficients": coefficients,
            "residual_std_error": round(float(np.sqrt(mse)), 4) if dof > 0 else None,
        },
        "sample_size": n,
        "execution_time_ms": elapsed,
    }
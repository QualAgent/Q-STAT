
import time
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from src.utils.validators import validate_data, validate_numeric_columns, clean_numeric_data

async def pca_analysis(
    target: str, # PCA에서는 Target이 필수가 아니지만, 인터페이스 통레를 위해 받음 (무시 가능)
    features: list[str],
    data: list[dict],
    options: dict | None = None,
) -> dict:
    """
    주성분 분석(PCA)을 수행합니다.
    
    Args:
        features: 분석할 수치형 변수 목록
        options: {"n_components": int (default: 2)}
    """
    start = time.time()
    options = options or {}
    n_components = options.get("n_components", 2)
    
    # Features 검증
    is_valid, error, df = validate_data(data, features)
    if not is_valid:
        return {"tool_name": "pca_analysis", "error": error, "execution_time_ms": 0}
        
    is_numeric, error = validate_numeric_columns(df, features)
    if not is_numeric:
        return {"tool_name": "pca_analysis", "error": error, "execution_time_ms": 0}
        
    df = clean_numeric_data(df, features)
    
    if len(df) < n_components:
        return {"tool_name": "pca_analysis", "error": f"Sample size ({len(df)}) less than n_components ({n_components})", "execution_time_ms": 0}

    try:
        # 데이터 표준화 (Standardization)
        x = df[features].values
        x = StandardScaler().fit_transform(x)
        
        # PCA 수행
        pca = PCA(n_components=n_components)
        principal_components = pca.fit_transform(x)
        
        # 결과 정리
        explained_variance_ratio = pca.explained_variance_ratio_.tolist()
        cumulative_variance_ratio = np.cumsum(explained_variance_ratio).tolist()
        
        # 성분별 기여도 (Loading) - 각 주성분에 대한 원본 변수의 기여도
        # components_: [n_components, n_features]
        loadings = pd.DataFrame(
            pca.components_.T, 
            columns=[f"PC{i+1}" for i in range(n_components)], 
            index=features
        ).to_dict()

        results = {
            "n_components": n_components,
            "explained_variance_ratio": explained_variance_ratio,
            "cumulative_variance_ratio": cumulative_variance_ratio,
            "loadings": loadings,
            # "principal_components": principal_components.tolist() # 데이터가 클 수 있으므로 제외하거나 필요시 옵션 처리
        }
        
    except Exception as e:
        return {"tool_name": "pca_analysis", "error": str(e), "execution_time_ms": int((time.time() - start) * 1000)}

    return {
        "tool_name": "pca_analysis",
        "results": results,
        "execution_time_ms": int((time.time() - start) * 1000)
    }

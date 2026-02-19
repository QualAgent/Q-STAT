
import asyncio
import numpy as np
import pandas as pd
from src.tools.correlation import correlation_analysis
from src.tools.regression import regression_analysis
from src.tools.anova import anova_test
from src.tools.t_test import t_test
from src.tools.chi_square import chi_square_test
from src.tools.pca import pca_analysis
from src.tools.time_series import time_series_analysis
from src.tools.control_chart import control_chart_analysis

def create_dummy_data():
    """테스트용 더미 데이터 생성"""
    np.random.seed(42)
    n = 100
    
    # 기본 데이터
    df = pd.DataFrame({
        "group": np.random.choice(["A", "B", "C"], n),
        "category1": np.random.choice(["X", "Y"], n),
        "category2": np.random.choice(["P", "Q"], n),
        "value1": np.random.normal(100, 10, n),
        "value2": np.random.normal(50, 5, n),
        "timestamp": pd.date_range("2024-01-01", periods=n, freq="D"),
    })
    
    # 상관관계 추가 (value3는 value1과 강한 양의 상관관계)
    df["value3"] = df["value1"] * 2 + np.random.normal(0, 5, n)
    
    return df.to_dict(orient="records")

async def run_tests():
    data = create_dummy_data()
    print(f"Loaded {len(data)} rows of dummy data.")
    print("-" * 50)

    # 1. Correlation Analysis
    print("\n[Test 1] Correlation Analysis")
    res = await correlation_analysis(
        target="value1",
        features=["value2", "value3"],
        data=data,
        options={"method": "pearson"}
    )
    print(res)

    # 2. Regression Analysis
    print("\n[Test 2] Regression Analysis")
    res = await regression_analysis(
        target="value3",
        features=["value1", "value2"],
        data=data
    )
    print(res)

    # 3. ANOVA
    print("\n[Test 3] ANOVA")
    res = await anova_test(
        target="value1",
        features=["group"],
        data=data
    )
    print(res)

    # 4. T-Test (Independent Group)
    print("\n[Test 4] T-Test (Group A vs B)")
    # A와 B 그룹만 필터링해서 테스트
    filtered_data = [d for d in data if d["group"] in ["A", "B"]]
    res = await t_test(
        target="value1",
        features=["group"],
        data=filtered_data,
        options={"paired": False}
    )
    print(res)

    # 5. Chi-Square Test
    print("\n[Test 5] Chi-Square Test")
    res = await chi_square_test(
        target="category1",
        features=["category2"],
        data=data
    )
    print(res)

    # 6. PCA
    print("\n[Test 6] PCA")
    res = await pca_analysis(
        target="", # PCA는 target 불필요
        features=["value1", "value2", "value3"],
        data=data,
        options={"n_components": 2}
    )
    print(res)

    # 7. Time Series
    print("\n[Test 7] Time Series Analysis")
    res = await time_series_analysis(
        target="value1",
        features=["timestamp"],
        data=data,
        options={"period": 7}
    )
    # 결과가 길 수 있으므로 요약만 출력
    print(res)

    # 8. Control Chart
    print("\n[Test 8] Control Chart")
    res = await control_chart_analysis(
        target="value1",
        features=[],
        data=data,
        options={"usl": 120, "lsl": 80, "sigma": 3}
    )
    print(res)

if __name__ == "__main__":
    asyncio.run(run_tests())

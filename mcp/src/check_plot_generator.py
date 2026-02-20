
import asyncio
import pandas as pd
import sys
import os
import json

# 현재 작업 디렉토리를 sys.path에 추가하여 src 모듈을 찾을 수 있게 함
sys.path.append(os.getcwd())

from src.tools.plot_generator import generate_plot

async def test_generate_plot():
    print("=== Testing Plot Generator ===")

    # 1. Scatter Plot (산점도)
    print("\n[1] Testing Scatter Plot...")
    # 데이터를 List[Dict] 형태(Records)로 준비
    df_scatter = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "y": [10, 20, 25, 30, 40, 50, 60, 70, 80, 90],
        "category": ["A", "A", "B", "B", "A", "B", "A", "B", "A", "B"]
    })
    data_scatter = df_scatter.to_dict(orient="records")
    
    try:
        res = await generate_plot(
            chart_type="scatter",       # 첫 번째 인자: 차트 타입
            data=data_scatter,          # 두 번째 인자: 데이터 (List[Dict])
            x_column="x",               # 필수 키워드 인자
            y_column="y",
            group_column="category",
            title="Test Scatter Plot",
            options={"save_path": "src/scatter_test.html"}
        )
        _check_result(res, "scatter")
    except Exception as e:
        print(f"❌ Scatter Plot Error: {e}")

    # 2. Control Chart (관리도)
    print("\n[2] Testing Control Chart...")
    df_control = pd.DataFrame({
        "time": range(1, 21),
        "value": [10 + (i%3) for i in range(20)]
    })
    # 이상치 추가
    df_control.loc[10, "value"] = 15
    data_control = df_control.to_dict(orient="records")

    try:
        res = await generate_plot(
            chart_type="control_chart",
            data=data_control,
            x_column="time",
            y_column="value",
            title="Process Control Chart",
            options={"ucl": 12, "lcl": 8, "center_line": 10, "save_path": "src/control_chart_test.html"}
        )
        _check_result(res, "control_chart")
    except Exception as e:
        print(f"❌ Control Chart Error: {e}")

def _check_result(res: dict, chart_type: str):
    if "error" in res:
        print(f"❌ {chart_type} failed: {res['error']}")
        return
    
    plotly_json = res.get("plotly_json")
    if plotly_json:
        # plotly_json은 딕셔너리 형태임
        print(f"✅ {chart_type} generated successfully.")
        print(f"   Keys: {plotly_json.keys()}")
        if 'data' in plotly_json:
            print(f"   Data points: {len(plotly_json['data'][0].get('x', []))}")
            # print(json.dumps(plotly_json, indent=2)[:200] + "...")
    else:
        print(f"❌ {chart_type} returned no plot_json")

if __name__ == "__main__":
    asyncio.run(test_generate_plot())

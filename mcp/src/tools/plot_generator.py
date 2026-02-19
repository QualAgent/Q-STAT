# mcp/src/tools/plot_generator.py
import time
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.utils.validators import validate_data


CHART_TYPES = [
    "scatter", "line", "bar", "histogram",
    "box", "heatmap", "control_chart",
]


async def generate_plot(
    chart_type: str,
    data: list[dict],
    x_column: str,
    y_column: str | None = None,
    group_column: str | None = None,
    title: str = "",
    options: dict | None = None,
) -> dict:
    """
    데이터를 기반으로 시각화를 생성합니다.

    Args:
        chart_type: 차트 유형 ("scatter" | "line" | "bar" | "histogram" |
                    "box" | "heatmap" | "control_chart")
        data: 차트에 사용할 데이터
        x_column: X축 컬럼명
        y_column: Y축 컬럼명 (histogram은 불필요)
        group_column: 그룹핑 컬럼 (선택)
        title: 차트 제목
        options: 추가 옵션 (UCL/LCL 등)

    Returns:
        {"chart_type": str, "plotly_json": dict, "execution_time_ms": int}
    """
    start = time.time()

    if chart_type not in CHART_TYPES:
        return {"error": f"지원하지 않는 차트 유형: {chart_type}. 가능: {CHART_TYPES}"}

    required = [x_column]
    if y_column and chart_type != "histogram":
        required.append(y_column)

    is_valid, error, df = validate_data(data, required)
    if not is_valid:
        return {"error": error}

    try:
        fig = _create_figure(chart_type, df, x_column, y_column, group_column, title, options)
        plotly_json = json.loads(fig.to_json())

        elapsed = int((time.time() - start) * 1000)
        return {
            "chart_type": chart_type,
            "plotly_json": plotly_json,
            "execution_time_ms": elapsed,
        }
    except Exception as e:
        return {"error": f"차트 생성 실패: {str(e)}"}


def _create_figure(chart_type, df, x_col, y_col, group_col, title, options):
    """차트 유형별 Plotly Figure 생성"""
    opts = options or {}

    if chart_type == "scatter":
        fig = px.scatter(df, x=x_col, y=y_col, color=group_col, title=title)

    elif chart_type == "line":
        fig = px.line(df, x=x_col, y=y_col, color=group_col, title=title)

    elif chart_type == "bar":
        fig = px.bar(df, x=x_col, y=y_col, color=group_col, title=title)

    elif chart_type == "histogram":
        fig = px.histogram(df, x=x_col, color=group_col, title=title,
                          nbins=opts.get("bins", 30))

    elif chart_type == "box":
        fig = px.box(df, x=group_col or x_col, y=y_col or x_col, title=title)

    elif chart_type == "heatmap":
        # 상관행렬 히트맵
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        corr_matrix = df[numeric_cols].corr()
        fig = px.imshow(corr_matrix, text_auto=".2f", title=title or "Correlation Heatmap")

    elif chart_type == "control_chart":
        fig = _create_control_chart(df, x_col, y_col, title, opts)

    else:
        fig = px.scatter(df, x=x_col, y=y_col, title=title)

    fig.update_layout(template="plotly_white")
    return fig


def _create_control_chart(df, x_col, y_col, title, opts):
    """SPC 관리도 차트"""
    import numpy as np

    values = df[y_col].values
    cl = opts.get("center_line", float(np.mean(values)))
    sigma = opts.get("sigma", float(np.std(values, ddof=1)))
    ucl = opts.get("ucl", cl + 3 * sigma)
    lcl = opts.get("lcl", cl - 3 * sigma)

    fig = go.Figure()

    # 데이터 포인트
    fig.add_trace(go.Scatter(
        x=df[x_col], y=values,
        mode="lines+markers", name="측정값",
        marker=dict(size=6),
    ))

    # 관리한계선
    x_range = [df[x_col].iloc[0], df[x_col].iloc[-1]]
    fig.add_trace(go.Scatter(x=x_range, y=[ucl, ucl],
                             mode="lines", name=f"UCL ({ucl:.2f})",
                             line=dict(dash="dash", color="red")))
    fig.add_trace(go.Scatter(x=x_range, y=[cl, cl],
                             mode="lines", name=f"CL ({cl:.2f})",
                             line=dict(dash="dot", color="green")))
    fig.add_trace(go.Scatter(x=x_range, y=[lcl, lcl],
                             mode="lines", name=f"LCL ({lcl:.2f})",
                             line=dict(dash="dash", color="red")))

    # 위반 포인트 강조
    violations = df[(values > ucl) | (values < lcl)]
    if len(violations) > 0:
        fig.add_trace(go.Scatter(
            x=violations[x_col], y=violations[y_col],
            mode="markers", name="위반",
            marker=dict(size=12, color="red", symbol="x"),
        ))

    fig.update_layout(title=title or "Control Chart", template="plotly_white")
    return fig
# mcp/src/server.py
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv

load_dotenv()

# MCP 서버 인스턴스 생성
mcp = FastMCP(
    name="Q-STAT Statistics Tools",
)

# --- 도구 등록 ---
# 각 도구 모듈에서 함수를 import하여 MCP 도구로 등록합니다.
# 아래는 등록 패턴 예시이며, 각 도구 구현 후 하나씩 추가합니다.

from src.tools.text_to_sql import text_to_sql
from src.tools.correlation import correlation_analysis
from src.tools.regression import regression_analysis
from src.tools.anova import anova_test
from src.tools.t_test import t_test
from src.tools.chi_square import chi_square_test
from src.tools.pca import pca_analysis
from src.tools.time_series import time_series_analysis
from src.tools.control_chart import control_chart_analysis
from src.tools.plot_generator import generate_plot

# MCP 도구 등록
mcp.tool()(text_to_sql)
mcp.tool()(correlation_analysis)
mcp.tool()(regression_analysis)
mcp.tool()(anova_test)
mcp.tool()(t_test)
mcp.tool()(chi_square_test)
mcp.tool()(pca_analysis)
mcp.tool()(time_series_analysis)
mcp.tool()(control_chart_analysis)
mcp.tool()(generate_plot)


if __name__ == "__main__":
    mcp.run(transport="sse")

import json
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from src.llm import get_llm
from src.state_schemas.nodes import (
    ProblemInfo,
    ColumnSelectionResult,
    ToolSelectionResult
)

# MCP 서버 주소 (Docker 내부 통신용)
MCP_SERVER_URL = "http://qstat_mcp:8000/sse"

class ToolSelectorAgent:
    def __init__(self):
        # 중앙화된 LLM 모듈 사용
        self.llm = get_llm()

    async def _fetch_available_tools(self) -> list[dict]:
        """MCP 서버에서 사용 가능한 도구 목록 조회"""
        try:
            # 421 Misdirected Request 방지를 위한 헤더 조작 (서버가 localhost만 허용할 경우)
            async with sse_client(url=MCP_SERVER_URL, headers={"Host": "localhost:8000"}) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    
                    tools_info = []
                    for tool in result.tools:
                        tools_info.append({
                            "name": tool.name,
                            "desc": tool.description or "설명 없음",
                        })
                    return tools_info
        except Exception as e:
            print(f"Error fetching tools from MCP server: {e}")
            return []

    async def select_tools(
        self, 
        problem_info: ProblemInfo, 
        columns_result: ColumnSelectionResult
    ) -> ToolSelectionResult:
        """
        문제 상황과 선택된 컬럼 정보를 바탕으로 최적의 통계 분석 도구를 매칭합니다.

        Args:
            problem_info: 문제 정의
            columns_result: 선택된 후보 컬럼 목록

        Returns:
            ToolSelectionResult TypedDict (assignments 리스트 포함)
        """
        
        selected_columns = columns_result.get("columns", [])
        if not selected_columns:
            return {"assignments": []}

        # 1. MCP 도구 목록 조회 (동적)
        available_tools = await self._fetch_available_tools()
        if not available_tools:
            print("No tools found from MCP server.")
            return {"assignments": []}

        # 프롬프트에 제공할 데이터 정리
        column_summaries = []
        for col in selected_columns:
            column_summaries.append({
                "column_name": col.get("column_name"),
                "reason": col.get("reason"),
                "data_summary": col.get("data_summary")
            })
            
        # 도구 목록 텍스트화
        tools_desc = "\n".join([f"- {t['name']}: {t['desc']}" for t in available_tools])

        prompt = ChatPromptTemplate.from_template("""
        당신은 통계 분석 전문가입니다.
        주어진 문제 상황과 선택된 데이터 컬럼들을 분석하여, 가장 적절한 통계 분석 도구를 매칭해주세요.

        [문제 상황]
        - 설명: {description}
        - 목표: {affected_parameter} 문제의 원인 규명

        [선택된 컬럼 목록]
        {columns}

        [사용 가능한 도구 목록 (실제 서버 제공)]
        {tools_desc}

        [요청사항]
        1. 각 컬럼에 대해 가장 적절한 분석 도구를 **하나씩** 선택하세요.
        2. 왜 그 도구를 선택했는지 논리적 이유(rationale)를 서술하세요. (예: "수치형 데이터이므로 상관분석이 적합", "시간에 따른 변화를 보기 위해 시계열 분석 선택" 등)
        3. mcp_server 이름은 "qstat_mcp"로 고정하세요.
        4. 결과는 반드시 아래 JSON 형식으로만 출력하세요.

        {{
            "assignments": [
                {{
                    "column_name": "컬럼명",
                    "tool_name": "도구명",
                    "mcp_server": "qstat_mcp",
                    "rationale": "선택 이유"
                }}
            ]
        }}
        """)

        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            result = chain.invoke({
                "description": problem_info.get("description"),
                "affected_parameter": problem_info.get("affected_parameter"),
                "columns": json.dumps(column_summaries, ensure_ascii=False, indent=2),
                "tools_desc": tools_desc
            })
            
            # 결과 반환 (ToolSelectionResult 타입에 맞춤)
            return {
                "assignments": result.get("assignments", [])
            }
            
        except Exception as e:
            print(f"Error in tool selection: {e}")
            return {"assignments": []}

# 테스트용 코드
if __name__ == "__main__":
    from datetime import datetime
    
    async def run_test():
        agent = ToolSelectorAgent()
        
        # 1. 더미 문제 정보
        problem_info: ProblemInfo = {
            "problem_code": "P-001",
            "description": "ETCHER_01 설비 식각률 저하. 가스 유량 변동 의심.",
            "process_name": "Etch",
            "equipment_id": "ETCHER_01",
            "lot_number": "LOT-001",
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "affected_parameter": "Etch Rate",
            "statistics": {},
            "severity": "high"
        }
        
        # 2. 더미 컬럼 선택 결과 (ColumnSelectorAgent의 출력 예시)
        columns_result: ColumnSelectionResult = {
            "columns": [
                {
                    "column_name": "gas_flow_total",
                    "reason": "식각률에 직접적 영향",
                    "score": 0.95,
                    "data_summary": {"min": 100, "max": 200, "avg": 150, "std": 10}
                },
                {
                    "column_name": "chamber_pressure",
                    "reason": "압력 변동은 반응 속도에 영향",
                    "score": 0.90,
                    "data_summary": {"min": 10, "max": 20, "avg": 15, "std": 2}
                }
            ],
            "strategy": "domain_knowledge"
        }
        
        print("Fetching tools and selecting...")
        result = await agent.select_tools(problem_info, columns_result)
        
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(run_test())

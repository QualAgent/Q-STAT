
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sqlalchemy import text
from src.llm import get_llm
from src.loader import engine
from src.state_schemas.nodes import ProblemInfo, ColumnSelectionResult

class ColumnSelectorAgent:
    def __init__(self):
        # 중앙화된 모듈 사용
        self.llm = get_llm()
        self.engine = engine
        
        # 사용 가능한 테이블 목록 (하드코딩하지 않고 DB에서 조회 가능하지만, 편의상 명시)
        self.available_tables = ["FDC", "PM", "MI", "BOM"]

    def _get_table_schema(self, table_name: str) -> list[str]:
        """안전한 SQL로 특정 테이블의 컬럼 목록만 조회"""
        if not table_name.replace("_", "").isalnum():
            print(f"Invalid table name: {table_name}")
            return []
            
        sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = :table_name
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), {"table_name": table_name})
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"Error fetching schema for {table_name}: {e}")
            return []

    def _select_target_table(self, problem_info: ProblemInfo) -> str:
        """문제 상황을 보고 가장 적절한 테이블 하나를 선택"""
        
        prompt = ChatPromptTemplate.from_template("""
        당신은 반도체 데이터 엔지니어입니다.
        주어진 문제 상황을 분석하기 위해 어떤 데이터 테이블을 조회해야 할지 판단하세요.

        [문제 정보]
        - 설명: {description}
        - 공정: {process_name}
        - 설비: {equipment_id}
        - 영향받은 파라미터: {affected_parameter}

        [사용 가능한 테이블]
        1. FDC (Fault Detection & Classification): 설비 센서 데이터 (가스, 압력, 온도 등)
        2. PM (Preventive Maintenance): 설비 유지보수 이력
        3. MI (Metrology Inspection): 계측 데이터 (CD, Thickness 등 결과값)
        4. BOM (Bill of Materials): 자재 정보

        [요청사항]
        - 위 문제의 원인을 파악하기 위해 가장 먼저 분석해야 할 테이블 하나를 선택하세요.
        - 결과는 JSON으로 반환하세요.

        {{
            "selected_table": "테이블명" (예: "FDC")
        }}
        """)

        chain = prompt | self.llm | JsonOutputParser()
        try:
            result = chain.invoke(problem_info) 
            table = result.get("selected_table", "FDC").upper()
            if table not in self.available_tables:
                return "FDC" # 기본값
            return table
        except Exception:
            return "FDC"

    def _calculate_statistics(self, table: str, column: str) -> dict:
        """선택된 컬럼의 기초 통계량 계산"""
        if not column.replace("_", "").isalnum():
            return {}
            
        sql = f"""
        SELECT 
            MIN("{column}") as min_val, 
            MAX("{column}") as max_val, 
            AVG("{column}") as avg_val, 
            STDDEV("{column}") as std_val
        FROM "{table}"
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql)).fetchone()
                if result:
                    return {
                        "min": float(result[0]) if result[0] is not None else 0.0,
                        "max": float(result[1]) if result[1] is not None else 0.0,
                        "avg": float(result[2]) if result[2] is not None else 0.0,
                        "std": float(result[3]) if result[3] is not None else 0.0,
                    }
        except Exception as e:
            print(f"Error calculating stats for {table}.{column}: {e}")
        return {}

    def select_candidate_columns(self, problem_info: ProblemInfo) -> ColumnSelectionResult:
        """
        문제 상황을 입력을 받아 연관성 높은 컬럼을 추천합니다.
        
        Args:
            problem_info: ProblemInfo TypedDict

        Returns:
            ColumnSelectionResult TypedDict
        """
        
        # 1. 대상 테이블 선정 (LLM 판단)
        target_table = self._select_target_table(problem_info)
        
        # 2. 스키마 조회
        columns = self._get_table_schema(target_table)
        if not columns:
            return {
                "columns": [],
                "strategy": "failed_no_table"
            }
            
        schema_text = ", ".join(columns)

        # 3. LLM Prompt 구성 (컬럼 선택)
        prompt = ChatPromptTemplate.from_template("""
        당신은 반도체 공정 데이터 분석 전문가입니다.
        주어진 문제 상황과 테이블 스키마를 보고, 원인 분석에 필요한 핵심 컬럼을 선택하세요.

        [문제 정보]
        - 설명: {description}
        - 공정: {process_name}
        - 설비: {equipment_id}
        - 영향받은 파라미터: {affected_parameter}

        [대상 테이블]
        - 이름: {table}
        - 전체 컬럼: {schema}

        [요청사항]
        1. 문제의 원인을 파악하거나 상관관계를 분석하기 위해 필요한 컬럼을 최대 5개 선택하세요.
        2. 각 컬럼별로 선택 이유와 예상되는 연관성 점수(0.0~1.0)를 부여하세요.
        3. 전략(strategy)은 당신이 이 컬럼들을 선택할 때 사용한 접근 방식을 간략히 작성하세요. (예: "correlation_based", "domain_knowledge" 등)
        4. 결과는 반드시 아래 JSON 형식으로만 출력하세요.

        {{
            "columns": [
                {{
                    "column_name": "컬럼명",
                    "reason": "구체적인 선택 이유",
                    "score": 0.95
                }}
            ],
            "strategy": "전략에 대한 설명"
        }}
        """)

        # 4. LLM 실행
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            result = chain.invoke({
                **problem_info,
                "table": target_table,
                "schema": schema_text
            })
            
            selected_columns = result.get("columns", [])
            strategy = result.get("strategy", "LLM based selection") # LLM이 생성한 전략 사용
            
            # 5. 후처리: 각 컬럼별 기초 통계량(data_summary) 계산
            final_columns = []
            for col_info in selected_columns:
                col_name = col_info.get("column_name")
                summary = self._calculate_statistics(target_table, col_name)
                
                final_columns.append({
                    "column_name": col_name,
                    "reason": col_info.get("reason", ""),
                    "score": col_info.get("score", 0.0),
                    "data_summary": summary 
                })

            return {
                "columns": final_columns,
                "strategy": strategy
            }
            
        except Exception as e:
            print(f"Error in column selection: {e}")
            return {
                "columns": [],
                "strategy": "error"
            }

# 테스트용 코드
if __name__ == "__main__":
    from datetime import datetime
    
    agent = ColumnSelectorAgent()
    
    # 더미 문제 정보
    problem_info: ProblemInfo = {
        "problem_code": "P-001",
        "description": "ETCHER_01 설비에서 식각률(Etch Rate)이 급격히 저하됨. 가스 공급 계통 의심.",
        "process_name": "Etch Process",
        "equipment_id": "ETCHER_01",
        "lot_number": "LOT-20240219-01",
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "affected_parameter": "Etch Rate",
        "statistics": {},
        "severity": "high"
    }
    
    result = agent.select_candidate_columns(problem_info)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

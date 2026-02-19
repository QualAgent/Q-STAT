# mcp/src/tools/text_to_sql.py
import json
import os
import re
from dotenv import load_dotenv
from src.utils.db import execute_query, get_table_schemas

load_dotenv()

MAX_RETRIES = 2


def _get_llm():
    """LLM 인스턴스 반환 (be/src/llm.py와 동일한 패턴)"""
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        )
    elif provider == "bedrock":
        from langchain_aws import ChatBedrockConverse
        return ChatBedrockConverse(
            model=os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-120b-1:0"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        )
    else:
        raise ValueError(f"지원하지 않는 LLM_PROVIDER: {provider}")


def _extract_sql(response: str) -> str:
    """LLM 응답에서 SQL 추출"""
    # 코드블록 안의 SQL
    sql_match = re.search(r'```(?:sql)?\s*([\s\S]*?)\s*```', response)
    if sql_match:
        return sql_match.group(1).strip()

    # SELECT로 시작하는 문장 추출
    select_match = re.search(r'(SELECT[\s\S]*?;)', response, re.IGNORECASE)
    if select_match:
        return select_match.group(1).strip()

    return response.strip()


async def text_to_sql(
    natural_query: str,
    target_db: str = "all",
    filters: dict | None = None,
) -> dict:
    """
    자연어 질의를 SQL로 변환하여 실행합니다.

    Args:
        natural_query: 자연어 질의 (ex. "ETCHER_01의 최근 7일 gas_flow_total 조회")
        target_db: 대상 테이블 ("MI" | "FDC" | "PM" | "BOM" | "all")
        filters: 추가 필터 조건 (선택)

    Returns:
        성공: {"sql": str, "data": list, "columns": list, "column_types": dict,
               "row_count": int, "execution_time_ms": int}
        실패: {"error": str, "failed_sql": str, "retry_count": int}
    """
    import time

    # 1. DB 스키마 정보 조회
    schemas = get_table_schemas()
    if not schemas:
        return {"error": "DB 스키마 조회 실패", "failed_sql": "", "retry_count": 0}

    # 대상 테이블 필터링
    if target_db != "all":
        target_upper = target_db.upper()
        schemas = {k: v for k, v in schemas.items() if k.upper() == target_upper}
        if not schemas:
            return {"error": f"테이블 '{target_db}'를 찾을 수 없습니다.", "failed_sql": "", "retry_count": 0}

    schema_text = _format_schema(schemas)

    # 2. LLM으로 SQL 생성
    llm = _get_llm()
    last_error = ""
    generated_sql = ""

    for attempt in range(MAX_RETRIES + 1):
        prompt = _build_prompt(natural_query, schema_text, filters, last_error, attempt)

        response = llm.invoke(prompt)
        generated_sql = _extract_sql(response.content)

        # 3. SQL 실행
        start_time = time.time()
        result = execute_query(generated_sql)
        elapsed_ms = int((time.time() - start_time) * 1000)

        if result["success"]:
            # 컬럼 타입 추출
            column_types = {}
            if result.get("data") and len(result["data"]) > 0:
                for col in result["columns"]:
                    sample = result["data"][0].get(col)
                    column_types[col] = type(sample).__name__ if sample is not None else "unknown"

            return {
                "sql": generated_sql,
                "data": result["data"],
                "columns": result["columns"],
                "column_types": column_types,
                "row_count": result["row_count"],
                "execution_time_ms": elapsed_ms,
            }
        else:
            last_error = result["error"]

    # 모든 재시도 실패
    return {
        "error": f"SQL 실행 실패 (재시도 {MAX_RETRIES}회): {last_error}",
        "failed_sql": generated_sql,
        "retry_count": MAX_RETRIES,
    }


def _format_schema(schemas: dict) -> str:
    """스키마를 LLM 프롬프트용 텍스트로 변환"""
    lines = []
    for table, columns in schemas.items():
        cols = ", ".join([f"{c['column']} ({c['type']})" for c in columns])
        lines.append(f"- {table}: {cols}")
    return "\n".join(lines)


def _build_prompt(query: str, schema: str, filters: dict | None, last_error: str, attempt: int) -> str:
    """SQL 생성 프롬프트 구성"""
    prompt = f"""당신은 PostgreSQL 전문가입니다. 자연어 질의를 SQL로 변환하세요.

[사용 가능한 테이블 및 컬럼]
{schema}

[질의]
{query}
"""

    if filters:
        prompt += f"\n[추가 필터]\n{json.dumps(filters, ensure_ascii=False)}\n"

    if attempt > 0 and last_error:
        prompt += f"""
[이전 시도 실패]
에러: {last_error}
위 에러를 수정하여 올바른 SQL을 다시 작성하세요.
"""

    prompt += """
규칙:
- SELECT 문만 허용 (INSERT, UPDATE, DELETE 금지)
- SQL만 출력하세요. 설명 없이 SQL 코드블록만 반환하세요.
- 테이블명과 컬럼명은 큰따옴표로 감싸세요 (PostgreSQL 대소문자 구분).
- LIMIT 1000을 기본으로 추가하세요 (대량 조회 방지).
"""
    return prompt
# Q-STAT Quality Agent (DMAIC)

## 1. WHAT & WHY
- **Goal**: 반도체 공정의 불량 원인(노후화/오염/센서)을 통계적으로 규명하는 AI 에이전트 개발.
- **Architecture**: Orchestrator + 4 Sub-Agents (Data Monitor, Stat Analyzer, Docs Researcher, Strategy Advisor)의 LangGraph 구조.
- **Context**: 사용자(엔지니어)는 통계 지식이 없으므로, 에이전트가 주도적으로 가설을 수립하고 검증해야 함.

## 2. HOW
### Tech Stack
- **Language**: Python 3.12+ (Type Hinting 필수)
- **Agent Framework**: LangGraph (Orchestration)
- **Frontend**: Vue.js 3 + Vite
- **Backend**: FastAPI + Uvicorn
- **Database**: PostgreSQL on Supabase (SQLAlchemy)
- **Data**: 4대 정규화 테이블 (Metrology, Sensor(FDC), Maintenance(PM), BOM)

### Essential Commands
- **Start All**: `docker compose up --build`
- **Backend Only**: `docker compose up be`
- **Frontend Only**: `docker compose up fe`
- **Load Data**: `docker compose exec be python -m src.loader` (엑셀 -> DB 적재)
- **Test**: `docker compose exec be pytest tests/`

### Directory Structure
- `be/src/main.py`: FastAPI 앱 진입점
- `be/src/agents/`: 에이전트 로직 (Orchestrator, Data Monitor, Stat Analyzer, Docs Researcher, Strategy Advisor)
- `be/src/routers/`: FastAPI 라우터 (API 엔드포인트)
- `be/src/tools/`: 에이전트가 사용하는 도구 (SQL Loader, Statistics Calc)
- `be/src/state.py`: **[중요]** 에이전트 간 공유되는 유일한 메모리 구조 (`AgentState`)
- `fe/src/`: Vue.js 컴포넌트 및 페이지


## 3. Coding Standards (for AI)
1. **Agnet별 R&R 엄수**:
    - `Monitor`: SQL 조회만 수행, 통계 분석 금지.
    - `Analyst`: 수치로 근거 제시.
2. **State 관리**:
    - 모든 함수는 `AgentState`를 인자로 받고, 변경된 값 반환할 것.
3. **잡담 금지**:
    -  이모지 출력 금지. 불필요한 서론/결론 생략. 수정된 코드 블록과 핵심 요약만 출력.

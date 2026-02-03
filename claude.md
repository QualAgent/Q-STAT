# Focus Ring Quality Agent (DMAIC)

## 1. WHAT & WHY (프로젝트 개요)
- **Goal**: 반도체 공정의 불량 원인(노후화/오염/센서)을 통계적으로 규명하는 AI 에이전트 개발.
- **Architecture**: Supervisor(관리자) + 3 Sub-Agents(감시/분석/보고)의 LangGraph 구조.
- **Context**: 사용자(엔지니어)는 통계 지식이 없으므로, 에이전트가 주도적으로 가설을 수립하고 검증해야 함.

## 2. HOW (개발 가이드)
### Tech Stack
- **Language**: Python 3.12+ (Type Hinting 필수)
- **Framework**: LangGraph (Orchestration), Streamlit (Frontend)
- **Database**: PostgreSQL (SQLAlchemy)
- **Data**: 4대 정규화 테이블 (Metrology, Sensor(FDC), Maintenance(PM), BOM)

### Essential Commands
- **Run App**: `streamlit run src/main.py`
- **Load Data**: `python src/loader_rdb.py` (엑셀 -> DB 적재)
- **Test**: `pytest tests/` (단위 테스트)

### Directory Structure (Progressive Disclosure)
- `src/agents/`: 에이전트 로직 (Supervisor, Monitor, Analyst, Reporter)
- `src/tools/`: 에이전트가 사용하는 도구 (SQL Loader, Statistics Calc)
- `src/state.py`: **[중요]** 에이전트 간 공유되는 유일한 메모리 구조 (`AgentState`)

## 3. Database Schema (Context)
SQL 작성 시 반드시 아래 테이블/컬럼명을 준수할 것.

| Table Name | Role | Key Columns |
| :--- | :--- | :--- |
| **`tb_metrology`** | **Target** (불량 판단) | `lot_id`, `cd_value` (Target Variable) |
| **`tb_sensor_data`** | **Feature** (원인 분석) | `lot_id`, `pressure`, `temp`, `bias_power` |
| **`tb_maintenance_log`** | **Context** (이력 확인) | `eqp_id`, `part_id`, `date`, `pm_type` |
| **`tb_part_bom`** | **Master** (수명 기준) | `part_id`, `life_limit` (수명), `unit` |

## 4. Coding Standards (for AI)
1. **R&R 엄수**:
    - `Monitor`: SQL 조회만 수행, 통계 분석 금지.
    - `Analyst`: `scipy` 활용, 반드시 `p-value`나 `상관계수` 등 수치로 근거 제시.
2. **State 관리**:
    - 모든 함수는 `AgentState`를 인자로 받고, 변경된 값만 딕셔너리로 반환할 것.
3. **잡담 금지**:
    - 불필요한 서론/결론 생략. 수정된 코드 블록과 핵심 요약만 출력. 이모지 출력 금지.
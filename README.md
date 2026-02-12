# 제조 품질 관리 에이전트 아키텍처 설계

## 1. 전체 시스템 개요

**Metrology 데이터 기반 품질 이상 감지 → 통계 분석 → 원인 추정 → 리포트 생성 → 대화형 QA**

까지의 워크플로우를 자동화하는 AI 에이전트 시스템

---

## 2. 아키텍처 구성도

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          LangGraph Orchestrator                              │
│                                                                              │
│  ┌──────────┐   ┌──────────┐   ┌───────────────┐   ┌─────────────────────┐   │
│  │ Monitor  │──▶│ Classify │──▶│  Statistics   │──▶│    Reporter       │   │
│  │  Node    │   │  Node    │   │    Agent      │   │     Agent           │   │
│  └──────────┘   └──────────┘   └───────────────┘   └─────────────────────┘   │
│       │              │          │    │    │    │         │    │    │         │
│       ▼              ▼          ▼    ▼    ▼    ▼         ▼    ▼    ▼         │
│   [Notifier]    [사내 RDB]  [RAG] [MCP] [MCP] [MCP]  [RAG] [Notifier]        │
│                             [Stats][T2SQL][Plot]            [지식DB]         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                              대화형 QA                                 │  │
│  │                                                                        │  │
│  │  ┌──────────┐                                                          │  │
│  │  │QA Router │──┬── DATA_LOOKUP ──▶ QA Executor (T2SQL+Plot)           │  │
│  │  │          │  ├── RESULT_DETAIL ▶ QA Executor (State)                │  │
│  │  │          │  ├── GENERAL_QA ───▶ QA Executor (RAG)                  │  │
│  │  │          │  └── RE_ANALYSIS ──▶ ReAnalysis Planner                 │  │
│  │  └──────────┘                            │                             │  │
│  │                                   ┌──────┴──────┐                      │  │
│  │                                   │entry_point  │                      │  │
│  │                                   │판단 후      │                      │  │
│  │                                   │Statistics   │                      │  │
│  │                                   │Agent 재진입  │                     │  │
│  │                                   └─────────────┘                      │  │
│  │                                                                        │  │
│  │  ┌──────────────┐                                                      │  │
│  │  │ Response Node│ ◀── 모든 경로의 결과 수렴                            │  │
│  │  └──────────────┘                                                      │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. MCP 서버 도구 구성

Statistics Agent와 QA Executor가 공유하는 MCP 도구들을 먼저 정의한다.

### 3.1 MCP 통계 도구 (Statistics Tools)- i facts 사용예정

| 도구명 | 기능 | 사용 주체 |
| --- | --- | --- |
| `correlation_analysis` | 상관분석 | Statistics Agent |
| `regression_analysis` | 회귀분석 | Statistics Agent |
| `anova_test` | 분산분석 | Statistics Agent |
| `t_test` | t-검정 | Statistics Agent |
| `chi_square_test` | 카이제곱 검정 | Statistics Agent |
| `pca_analysis` | 주성분분석 | Statistics Agent |
| `time_series_decomposition` | 시계열 분해 | Statistics Agent |
| `control_chart_analysis` | 관리도 분석 | Statistics Agent |

### 3.2 MCP 데이터 도구 (Data Tools) — 공유 도구

| 도구명 | 기능 | 사용 주체 |
| --- | --- | --- |
| `text_to_sql` | 자연어 → SQL 변환 및 실행 | Statistics Agent, QA Executor |
| `plot_generator` | 데이터 시각화 자료 생성 | Statistics Agent, QA Executor |

### 3.2.1 text_to_sql 도구 상세

```python
@mcp_tool
def text_to_sql(
    natural_query: str,       # "ETCH-01 장비의 최근 일주일 gas flow"
    target_db: str,           # "eqp_sensor" | "metrology" | "material" | "process"
    filters: dict = None,     # 추가 필터 조건 (선택)
) -> dict:
    """
    내부 동작 (MCP 서버 측):
      1. target_db의 스키마 조회
      2. LLM으로 SQL 생성
      3. SQL 실행
      4. 실패 시 에러 분석 → SQL 수정 → 재시도 (최대 3회)
      5. 결과 반환
    """
    return {
        "sql": "SELECT timestamp, gas_flow_rate FROM ...",
        "data": [{"timestamp": "...", "gas_flow_rate": 45.2}, ...],
        "columns": ["timestamp", "gas_flow_rate"],
        "column_types": {"timestamp": "datetime", "gas_flow_rate": "float"},
        "row_count": 168,
        "execution_time_ms": 230,
    }
```

### 3.2.2 plot_generator 도구 상세

```python
@mcp_tool
def plot_generator(
    data: list[dict],         # text_to_sql 결과 등
    chart_type: str,          # "line" | "scatter" | "bar" | "histogram" | "heatmap" | "control_chart"
    x: str,                   # x축 컬럼
    y: str | list[str],       # y축 컬럼 (다중 가능)
    title: str = None,
    options: dict = None,     # 축 범위, 색상, 관리한계선 등
) -> dict:
    return {
        "image_url": "/plots/abc123.png",
        "image_base64": "...",
        "chart_type": "line",
        "data_summary": {"x_range": [...], "y_range": [...]},
    }
```

---

## 4. 노드/에이전트 상세 설계

### 4.1 Monitor Node (감시 노드) — `Step 1~2`

> **유형: LangGraph Node (비-LLM)**
LLM이 필요 없는 규칙 기반 로직이므로 일반 노드로 구현
> 

| 항목 | 내용 |
| --- | --- |
| **역할** | Metrology 데이터 스트림을 SPC 관리도 기준으로 모니터링하여 이상 감지 |
| **입력** | Metrology 측정 데이터 (RDB 또는 스트리밍) |
| **처리** | SPC Rule 위반 체크 (Nelson Rules, Western Electric Rules 등) |
| **출력** | 이상 감지 이벤트 (위반 유형, 해당 데이터 포인트, 시간, 공정/장비 정보) |
| **외부 연동** | Notifier 서비스 → 엔지니어 이메일/Slack 알림 발송 |

```python
class MonitorNode:
    def run(self, state):
        data = fetch_metrology_data()
        violations = spc_check(data, rules=state["spc_rules"])
        if violations:
            notify_engineer(violations)
            return {"violations": violations, "raw_data": data, "goto": "classify"}
        return {"goto": "END"}
```

**설계 포인트:**

- 주기적 polling 또는 이벤트 트리거 방식 선택 가능
- SPC 룰은 설정 파일/DB로 관리 (관리도 종류, 관리한계선 등)
- 이 노드는 LangGraph의 **진입점(Entry Point)** 역할

---

### 4.2 Classify Node (문제 분류 노드) — `Step 3`

> **유형: LangGraph Node (LLM 사용)**
감지된 이상을 해석하고 구조화된 문제 설명을 생성
> 

| 항목 | 내용 |
| --- | --- |
| **역할** | 감지된 이상 데이터를 분석하여 문제 유형 분류 및 컨텍스트 정보 수집 |
| **입력** | Monitor Node의 이상 감지 이벤트 + Raw Data |
| **처리** | ① 이상 유형 분류 (Drift, Shift, Out-of-Spec 등)
② 관련 공정/자재/장비 정보 조회
③ 문제 상황 자연어 요약 생성 |
| **출력** | 구조화된 문제 정의서 (Problem Context) |
| **외부 연동** | 사내 RDB (공정 정보, 자재 정보, 장비 이력 등) |

```python
problem_context = {
    "issue_type": "CD_DRIFT",
    "description": "Layer3 CD 값이 지속적으로 상승 추세를 보이며...",
    "affected_process": "ETCH-01",
    "equipment_id": "EQP-A301",
    "material_lot": "LOT-20250210-A",
    "time_range": ["2025-02-10T08:00", "2025-02-10T14:00"],
    "data_summary": { ... },
}
```

**설계 포인트:**

- LLM이 데이터 패턴을 해석하여 문제 유형을 분류
- 공정/자재/장비 정보는 RDB 조회로 풍부한 컨텍스트 확보
- 이 노드의 출력이 이후 모든 노드의 **공유 컨텍스트** 역할

---

### 4.3 Statistics Agent (통계 분석 에이전트) — `Step 4`

> **유형: LangGraph Sub-Agent (LLM + Tool Use)**
> 

내부적으로 3개의 서브 노드로 구성:

```
┌─ Statistics Agent ──────────────────────────────────────┐
│                                                          │
│  [4-1. Column Selector]                                  │
│         │  RAG + LLM                                     │
│         ▼                                                │
│  [4-2. Tool Selector]                                    │
│         │  LLM → MCP Tool 선택                           │
│         ▼                                                │
│  [4-3. Executor]                                         │
│         │  MCP Tool 호출:                                │
│         │    • text_to_sql (데이터 조회)                  │
│         │    • 통계 도구 (correlation, regression 등)     │
│         │  → 통계 결과 반환                              │
│         ▼                                                │
│  (반복 가능: 추가 분석 필요 시 4-1로 회귀)               │
│                                                          │
│  ※ reanalysis_plan이 존재하면 entry_point부터 재진입     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4.3.1 Column Selector (후보 변수 선정)

| 항목 | 내용 |
| --- | --- |
| **역할** | 문제와 연관될 가능성이 있는 데이터 컬럼/변수 후보군 선정 |
| **입력** | Problem Context + 사내 문서 RAG 검색 결과 (+ reanalysis_plan의 override_columns) |
| **처리** | RAG로 사내 문서 검색 → 관련 변수/파라미터 후보 추출 → LLM이 판단하여 최종 후보 리스트 생성. reanalysis_plan의 override_columns가 있으면 기존 후보에 반영 |
| **출력** | 분석 대상 후보 컬럼 리스트 + 선정 근거 |
| **외부 연동** | RAG (사내 기술문서, SOP, 과거 분석 리포트), 사내 RDB 스키마 정보 |

```python
# 최초 실행 시
candidate_columns = [
    {"column": "gas_flow_rate", "source_db": "eqp_sensor", "reason": "사내 SOP에 따르면 ..."},
    {"column": "chamber_pressure", "source_db": "eqp_sensor", "reason": "과거 분석 리포트에서 ..."},
    {"column": "rf_power", "source_db": "eqp_sensor", "reason": "..."},
    {"column": "wafer_thickness", "source_db": "material", "reason": "..."},
]

# reanalysis_plan.override_columns = {"add": ["esc_temp"], "remove": ["rf_power"]} 인 경우
# → 기존 후보에서 rf_power 제거, esc_temp 추가하여 재구성
```

### 4.3.2 Tool Selector (통계 기법 선택)

| 항목 | 내용 |
| --- | --- |
| **역할** | 현재 문제 유형과 데이터 특성에 맞는 최적의 통계 분석 기법 선택 |
| **입력** | Problem Context + 후보 컬럼 리스트 + MCP 서버 가용 도구 목록 (+ reanalysis_plan의 override_tools) |
| **처리** | LLM이 문제 유형/데이터 특성 고려하여 MCP 서버의 통계 도구 중 적절한 것 선택. override_tools가 있으면 강제 포함/제외 반영 |
| **출력** | 선택된 통계 도구 + 실행 파라미터 |
| **외부 연동** | MCP Server (도구 목록 조회) |

```python
# 최초 실행 시
selected_tools = [
    {"tool": "correlation_analysis", "params": {"target": "cd_value", "features": [...]}},
    {"tool": "regression_analysis", "params": {"target": "cd_value", "features": [...]}},
]

# reanalysis_plan.override_tools = {"force_include": ["pca_analysis"]} 인 경우
# → LLM이 기존 도구 유지 여부 판단 + pca_analysis 강제 추가
```

### 4.3.3 Executor (통계 실행 및 결과 반환)

| 항목 | 내용 |
| --- | --- |
| **역할** | MCP Tool을 호출하여 실제 통계 분석 실행 후 Raw 결과 반환 |
| **입력** | 선택된 통계 도구 + 파라미터 + 후보 컬럼 정보 |
| **처리** | ① `text_to_sql`로 후보 컬럼의 실제 데이터 조회 ② 통계 도구로 분석 실행 |
| **출력** | 통계 분석 Raw 결과 (수치, p-value, 계수 등) — **해석 없이 결과만** |
| **외부 연동** | MCP Server: `text_to_sql` + 통계 도구 실행 |

```python
# Executor 동작 흐름
# 1) 데이터 조회 (MCP: text_to_sql)
data = mcp_call("text_to_sql", {
    "natural_query": "ETCH-01 장비의 gas_flow_rate, chamber_pressure 최근 7일",
    "target_db": "eqp_sensor"
})

# 2) 통계 분석 실행 (MCP: 통계 도구)
stat_results = {
    "correlation_analysis": {
        "gas_flow_rate": {"r": 0.87, "p_value": 0.001},
        "chamber_pressure": {"r": 0.42, "p_value": 0.045},
    },
    "regression_analysis": {
        "r_squared": 0.82,
        "coefficients": {"gas_flow_rate": 1.23, "chamber_pressure": 0.45},
        "f_statistic": 34.7,
        "p_value": 0.0001,
    }
}
```

### 4.3.4 Statistics Agent의 재진입 처리 로직

reanalysis_plan이 State에 존재하면, entry_point에 따라 해당 서브노드부터 실행을 시작합니다:

```python
class StatisticsAgent:
    def run(self, state):
        plan = state.get("reanalysis_plan")

        if plan:
            entry = plan["entry_point"]

            # 데이터 조건 변경이 있으면 problem_context 업데이트
            if plan.get("override_filters"):
                state["problem_context"].update(plan["override_filters"])

            if entry == "executor":
                return self.executor(state)         # 동일 조건 재실행
            elif entry == "tool_selector":
                return self.tool_selector(state)    # 도구 선택부터
            elif entry == "column_selector":
                return self.column_selector(state)  # 컬럼 선정부터
        else:
            return self.column_selector(state)      # 최초 실행
```

**설계 포인트 (Statistics Agent 전체):**

- 반복 루프 가능: Executor 결과가 불충분하면 Column Selector로 돌아가 추가 변수 탐색
- LLM의 역할은 "어떤 데이터를 볼지", "어떤 기법을 쓸지" **판단**하는 것
- 실제 데이터 조회는 `text_to_sql`, 통계 연산은 통계 MCP Tool이 수행
- 결과는 해석 없이 순수 통계값만 출력 → 해석은 Reporter Agent가 담당
- **재분석 시**: reanalysis_plan의 entry_point에 따라 내부 서브노드를 선택적으로 재진입

---

### 4.4 Reporter Agent (리포트 생성 에이전트) — `Step 5`

> **유형: LangGraph Sub-Agent (LLM + RAG + Tool Use)**
통계 결과 해석, 대응방안 제시, 리포트 생성까지 담당
> 

내부적으로 3개의 서브 노드로 구성:

```
┌─ Reporter Agent ────────────────────────────────────────┐
│                                                          │
│  [5-1. Interpreter]                                      │
│         │  통계 결과 → 자연어 해석 + 시각화              │
│         ▼                                                │
│  [5-2. Action Advisor]                                   │
│         │  RAG 기반 대응방안 제시                        │
│         ▼                                                │
│  [5-3. Report Generator]                                 │
│         │  최종 리포트 생성 + 알림 발송 + 지식 축적      │
│                                                          │
│  ※ RE_ANALYSIS 경유 시: Interpreter만 실행 후 Response로 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4.4.1 Interpreter (통계 결과 해석)

| 항목 | 내용 |
| --- | --- |
| **역할** | Statistics Agent의 Raw 통계 결과를 엔지니어가 이해할 수 있는 자연어로 해석 |
| **입력** | 통계 Raw 결과 + Problem Context |
| **처리** | LLM이 통계 결과 해석 + `plot_generator`로 시각화 생성 |
| **출력** | 자연어 해석 + 시각화 이미지 |
| **외부 연동** | MCP: `plot_generator` |

```python
interpretation = {
    "summary": "CD drift의 주요 원인은 gas_flow_rate로 판단됩니다 (r=0.87, p<0.01).",
    "key_factors": [
        {"column": "gas_flow_rate", "impact": "HIGH", "detail": "상관계수 0.87로 강한 양의 상관..."},
        {"column": "chamber_pressure", "impact": "MEDIUM", "detail": "..."},
    ],
    "plots": [
        {"image_url": "/plots/scatter_gasflow_cd.png", "description": "Gas Flow vs CD scatter"},
        {"image_url": "/plots/control_chart_cd.png", "description": "CD 관리도"},
    ]
}
```

### 4.4.2 Action Advisor (대응방안 제시)

| 항목 | 내용 |
| --- | --- |
| **역할** | 분석 결과를 기반으로 구체적인 대응 조치 제안 |
| **입력** | 해석 결과 + RAG 검색 (사내 SOP, 과거 대응 이력) |
| **처리** | RAG로 유사 사례/SOP 검색 → LLM이 맞춤형 대응방안 생성 |
| **출력** | 대응방안 리스트 (담당자, 조치 내용, 우선순위) |
| **외부 연동** | RAG (사내 SOP, 과거 대응 이력, 담당자 정보) |

```python
actions = [
    {
        "priority": 1,
        "action": "ETCH-01 장비 Gas MFC 교정 점검",
        "assignee": "설비팀 김OO (내선 1234)",
        "reference": "SOP-ETCH-042 Section 3.2",
        "deadline": "즉시",
    },
    {
        "priority": 2,
        "action": "Gas 공급 라인 Leak 점검",
        "assignee": "설비팀 박OO (내선 1235)",
        "reference": "PM Checklist #ETH-017",
        "deadline": "24시간 이내",
    },
]
```

### 4.4.3 Report Generator (리포트 생성 및 배포)

| 항목 | 내용 |
| --- | --- |
| **역할** | 전체 분석 과정을 종합 리포트로 생성 + 알림 + 지식DB 축적 |
| **입력** | Problem Context + 통계 결과 + 해석 + 시각화 + 대응방안 |
| **처리** | ① 리포트 문서 생성 ② 엔지니어 알림 발송 ③ 지식DB 저장 |
| **출력** | 최종 리포트 (PDF/HTML) |
| **외부 연동** | Notifier, 사내 지식DB, Vue 프론트엔드 |

```python
report_structure = {
    "title": "품질 이상 분석 리포트 - ETCH CD Drift",
    "timestamp": "2025-02-11T15:30:00",
    "sections": [
        "1. 문제 감지 개요",
        "2. 문제 분류 및 상세",
        "3. 통계 분석 과정 및 결과 (시각화 포함)",
        "4. 핵심 원인 분석",
        "5. 권장 대응 조치",
        "6. 참고 문서 및 이력",
    ]
}
```

---

### 4.5 대화형 QA 시스템 — `Step 6`

> **유형: LangGraph 노드 체인 (Router → Executor/Planner → Response)**
엔지니어가 분석 결과에 대해 추가 질문하는 대화형 인터페이스
> 

Step 6은 QA Router를 중심으로 4가지 intent 경로와 RE_ANALYSIS 전용 ReAnalysis Planner로 구성됩니다.

```
┌─ Step 6: 대화형 QA 시스템 ──────────────────────────────────────────────┐
│                                                                          │
│  사용자 질문                                                             │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────┐                        │
│  │           QA Router Node (LLM)               │                        │
│  │                                              │                        │
│  │  질문 분석 → intent 분류:                    │                        │
│  │    • DATA_LOOKUP   (데이터 조회/시각화)      │                        │
│  │    • RESULT_DETAIL (기존 결과 상세)          │                        │
│  │    • RE_ANALYSIS   (추가/재분석 요청)        │                        │
│  │    • GENERAL_QA    (일반 질문)               │                        │
│  └──┬───────┬────────────┬──────────────┬───────┘                        │
│     │       │            │              │                                │
│   DATA   RESULT      RE_ANALYSIS     GENERAL                            │
│     │       │            │              │                                │
│     ▼       ▼            ▼              ▼                                │
│  ┌──────┐ ┌──────┐ ┌──────────────────────────────┐ ┌──────┐            │
│  │QA Ex.│ │QA Ex.│ │   ReAnalysis Planner (LLM)   │ │QA Ex.│            │
│  │T2SQL │ │State │ │                              │ │RAG   │            │
│  │+Plot │ │참조  │ │  사용자 요청 파싱:            │ │+State│            │
│  └──┬───┘ └──┬───┘ │   • 변경할 변수 (컬럼)      │ └──┬───┘            │
│     │        │     │   • 변경할 통계 기법         │    │                │
│     │        │     │   • 변경할 데이터 조건       │    │                │
│     │        │     │   • 변경 없음 (동일 재실행)  │    │                │
│     │        │     │                              │    │                │
│     │        │     │  → reanalysis_plan 생성      │    │                │
│     │        │     │  → entry_point 결정          │    │                │
│     │        │     └──────────────┬───────────────┘    │                │
│     │        │                    │                     │                │
│     │        │                    ▼                     │                │
│     │        │           Statistics Agent               │                │
│     │        │           (entry_point부터 재진입)        │                │
│     │        │                    │                     │                │
│     │        │                    ▼                     │                │
│     │        │              Interpreter                 │                │
│     │        │              (해석만 수행)                │                │
│     │        │                    │                     │                │
│     └────────┴────────────────────┴─────────────────────┘                │
│                        │                                                 │
│                        ▼                                                 │
│              ┌──────────────────┐                                        │
│              │  Response Node   │                                        │
│              │  (답변 포맷팅)    │                                        │
│              └────────┬─────────┘                                        │
│                       ▼                                                  │
│                사용자에게 응답                                            │
│              (+ 추가 질문 대기)                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.5.1 QA Router Node (질문 분류)

| 항목 | 내용 |
| --- | --- |
| **역할** | 사용자 질문의 의도를 분류하여 적절한 처리 경로로 라우팅 |
| **입력** | 사용자 질문 + 대화 이력 |
| **처리** | LLM이 질문을 4가지 intent 중 하나로 분류 |
| **출력** | intent 라벨 + 파싱된 질문 파라미터 |

```python
intent_examples = {
    "DATA_LOOKUP": [
        "ETCH-01 장비의 gas flow 데이터 보여줘",
        "최근 일주일 CD 측정값 추이 그래프로 보여줘",
        "LOT-20250210-A의 wafer thickness 분포 보여줘",
    ],
    "RESULT_DETAIL": [
        "상관분석 결과 중 chamber_pressure 더 자세히 설명해줘",
        "왜 gas_flow_rate가 주요 원인이라고 판단한 거야?",
        "회귀분석 R² 값이 뭘 의미하는 거야?",
    ],
    "RE_ANALYSIS": [
        "같은 조건으로 다시 돌려봐",
        "rf_power도 추가해서 다시 해봐",
        "이번엔 PCA로 해봐",
        "최근 3일만 잘라서 다시 해봐",
        "ETCH-02 장비 데이터로도 해봐",
    ],
    "GENERAL_QA": [
        "과거에 비슷한 문제 있었어?",
        "ETCH 공정에서 CD drift 주요 원인이 보통 뭐야?",
        "SOP에 이런 경우 어떻게 하라고 되어 있어?",
    ],
}
```

### 4.5.2 QA Executor Node (질문 실행 — DATA, RESULT, GENERAL)

| 항목 | 내용 |
| --- | --- |
| **역할** | intent에 따라 적절한 도구를 사용하여 질문에 대한 답변 데이터 생성 |
| **입력** | intent + 파싱된 질문 + 전체 State |
| **처리** | intent별로 다른 도구 세트를 사용 |
| **출력** | 답변 데이터 (텍스트, 테이블, 시각화 등) |

| Intent | 사용 도구 | 동작 |
| --- | --- | --- |
| DATA_LOOKUP | `text_to_sql` + `plot_generator` | DB에서 데이터 조회 → 시각화 생성 |
| RESULT_DETAIL | State 참조 (도구 불필요) | 기존 분석 결과에서 상세 설명 생성 |
| GENERAL_QA | RAG 검색 + State 참조 | 사내 문서 검색 + 기존 컨텍스트 활용 |

```python
# DATA_LOOKUP 실행 예시
# 사용자: "ETCH-01 gas flow 추이 보여줘"

# 1) text_to_sql로 데이터 조회
data_result = mcp_call("text_to_sql", {
    "natural_query": "ETCH-01 장비의 gas_flow_rate 최근 7일 시간순",
    "target_db": "eqp_sensor"
})

# 2) plot_generator로 시각화
plot_result = mcp_call("plot_generator", {
    "data": data_result["data"],
    "chart_type": "line",
    "x": "timestamp",
    "y": "gas_flow_rate",
    "title": "ETCH-01 Gas Flow Rate Trend (최근 7일)"
})
```

### 4.5.3 ReAnalysis Planner Node (재분석 계획 수립 — RE_ANALYSIS 전용)

| 항목 | 내용 |
| --- | --- |
| **역할** | 사용자의 재분석 요청을 파싱하여 Statistics Agent의 재진입 조건 구성 |
| **입력** | 사용자의 재분석 요청 + 기존 분석 State (candidate_columns, selected_tools, problem_context) |
| **처리** | LLM이 기존 분석 조건과 사용자 요청을 비교하여 변경 사항 추출 → entry_point 및 override 파라미터 결정 |
| **출력** | reanalysis_plan (State에 저장) |

**RE_ANALYSIS 4가지 케이스:**

| 케이스 | 사용자 발화 예시 | 변경되는 것 | entry_point |
| --- | --- | --- | --- |
| **A. 동일 재실행** | "같은 조건으로 다시 돌려봐" | 없음 | `executor` |
| **B. 변수 변경** | "rf_power도 추가해서 다시 해봐" | 후보 컬럼 | `column_selector` |
| **C. 기법 변경** | "이번엔 PCA로 해봐" | 통계 도구 | `tool_selector` |
| **D. 데이터 조건 변경** | "최근 3일만 잘라서", "ETCH-02로 해봐" | 데이터 범위/대상 | `column_selector` |

```python
# 케이스별 reanalysis_plan 출력 예시

# A. 동일 재실행
reanalysis_plan = {
    "entry_point": "executor",
    "override_columns": None,
    "override_tools": None,
    "override_filters": None,
    "user_instruction": "동일 조건 재실행",
}

# B. 변수 변경
reanalysis_plan = {
    "entry_point": "column_selector",
    "override_columns": {
        "add": ["rf_power", "esc_temp"],
        "remove": [],
        "replace_all": False,           # 기존 컬럼 유지하면서 추가
    },
    "override_tools": None,
    "override_filters": None,
    "user_instruction": "rf_power, ESC 온도 추가 분석",
}

# C. 기법 변경
reanalysis_plan = {
    "entry_point": "tool_selector",
    "override_columns": None,
    "override_tools": {
        "force_include": ["pca_analysis"],
        "force_exclude": [],
    },
    "override_filters": None,
    "user_instruction": "PCA 분석 추가 수행",
}

# D. 데이터 조건 변경
reanalysis_plan = {
    "entry_point": "column_selector",
    "override_columns": None,
    "override_tools": None,
    "override_filters": {
        "time_range": ["2025-02-08T00:00", "2025-02-11T00:00"],
        "equipment_id": "EQP-A302",
    },
    "user_instruction": "ETCH-02 장비, 최근 3일 데이터로 재분석",
}
```

### 4.5.4 RE_ANALYSIS 실행 흐름

```
ReAnalysis Planner
        │
        │ reanalysis_plan 생성
        ▼
 Statistics Agent
 (entry_point에 따라 재진입)
        │
        │                   ┌─ entry_point = "executor" ─────▶ Executor만 실행
        ├── 재진입 분기 ────┤─ entry_point = "tool_selector" ▶ Tool Selector → Executor
        │                   └─ entry_point = "column_selector" ▶ Column Selector → Tool Selector → Executor
        │
        ▼
  Interpreter (해석만 수행)
        │
        ▼
  Response Node (포맷팅 → 사용자 응답)
```

**설계 포인트:**

- ReAnalysis Planner가 "무엇이 변경되었는지" 파싱하는 책임 전담
- Statistics Agent는 plan에 따라 실행만 수행 → 역할 분리 명확
- 재분석 경로에서는 Reporter Agent의 Action Advisor, Report Generator는 건너뛰고 **Interpreter만 실행** (재분석 결과 해석만 필요하므로)

### 4.5.5 Response Node (응답 포맷팅)

| 항목 | 내용 |
| --- | --- |
| **역할** | 모든 경로(DATA, RESULT, RE_ANALYSIS, GENERAL)의 결과를 사용자 친화적 형태로 포맷팅 |
| **입력** | QA Executor 또는 Interpreter의 결과 |
| **처리** | LLM이 결과를 자연어 + 시각화로 구성 |
| **출력** | 최종 응답 (프론트엔드 렌더링용) |

---

## 5. LangGraph State 설계

```python
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import add_messages

class QualityAgentState(TypedDict):
    # === Step 1-2: Monitor ===
    raw_data: dict                          # Metrology 원본 데이터
    spc_rules: dict                         # SPC 관리도 규칙 설정
    violations: List[dict]                  # 감지된 이상 목록

    # === Step 3: Classify ===
    problem_context: dict                   # 구조화된 문제 정의

    # === Step 4: Statistics ===
    candidate_columns: List[dict]           # 후보 변수 리스트
    selected_tools: List[dict]              # 선택된 통계 도구
    stat_results: dict                      # 통계 분석 Raw 결과
    fetched_data: dict                      # text_to_sql로 조회한 데이터 캐시
    analysis_iteration: int                 # 반복 분석 횟수

    # === Step 5: Reporter ===
    interpretation: dict                    # 통계 해석 결과
    plots: List[dict]                       # 생성된 시각화 목록
    recommended_actions: List[dict]         # 대응방안
    report: dict                            # 최종 리포트

    # === Step 6: Interactive QA ===
    messages: Annotated[list, add_messages] # 대화 이력
    current_query: Optional[str]            # 현재 사용자 질문
    current_intent: Optional[str]           # 분류된 intent
    reanalysis_plan: Optional[dict]         # 재분석 계획 (RE_ANALYSIS 시)
    qa_response: Optional[dict]             # QA 응답 데이터

    # === Step 4 이력 관리 (재분석 비교용) ===
    analysis_history: List[dict]            # 과거 분석 결과 이력
```

---

## 6. LangGraph 흐름도

```
           ┌──────────┐
           │  START    │
           └────┬─────┘
                ▼
        ┌──────────────┐     이상 없음
        │ Monitor Node │ ──────────────▶ END
        └──────┬───────┘
               │ 이상 감지 + 알림 발송
               ▼
        ┌──────────────┐
        │ Classify Node│
        └──────┬───────┘
               ▼
    ┌─────────────────────┐
    │  Statistics Agent    │◀─────────────────────────────────────────┐
    │  ┌────────────────┐ │                                          │
    │  │ Column Selector│ │  ◀── entry_point="column_selector"       │
    │  └───────┬────────┘ │                                          │
    │          ▼          │                                          │
    │  ┌────────────────┐ │                                          │
    │  │ Tool Selector  │ │  ◀── entry_point="tool_selector"        │
    │  └───────┬────────┘ │                                          │
    │          ▼          │                                          │
    │  ┌────────────────┐ │                                          │
    │  │   Executor     │─┼── 내부 반복 루프                         │
    │  │ (MCP: T2SQL +  │ │  ◀── entry_point="executor"             │
    │  │  통계 도구)     │ │                                          │
    │  └────────────────┘ │                                          │
    └─────────┬───────────┘                                          │
              ▼                                                      │
    ┌─────────────────────┐                                          │
    │   Reporter Agent    │                                          │
    │  ┌────────────────┐ │  ◀── RE_ANALYSIS 경유 시 여기만 실행     │
    │  │  Interpreter   │ │                                          │
    │  │ (MCP: Plot Gen)│ │                                          │
    │  └───────┬────────┘ │                                          │
    │          ▼          │                                          │
    │  ┌────────────────┐ │                                          │
    │  │ Action Advisor │ │  (최초 실행 시에만)                       │
    │  │ (RAG)          │ │                                          │
    │  └───────┬────────┘ │                                          │
    │          ▼          │                                          │
    │  ┌────────────────┐ │                                          │
    │  │Report Generator│ │  (최초 실행 시에만)                       │
    │  └────────────────┘ │                                          │
    └─────────┬───────────┘                                          │
              ▼                                                      │
    ┌─────────────────────────────┐                                  │
    │  QA Router                  │                                  │
    │  (intent 분류)              │                                  │
    └──┬──────┬──────┬──────┬────┘                                   │
       │      │      │      │                                        │
     DATA  RESULT  RE_AN  GENERAL                                    │
       │      │      │      │                                        │
       ▼      ▼      │      ▼                                        │
    ┌────────────┐   │   ┌────────────┐                              │
    │QA Executor │   │   │QA Executor │                              │
    │T2SQL + Plot│   │   │RAG + State │                              │
    └─────┬──────┘   │   └─────┬──────┘                              │
          │          │         │                                     │
          │          ▼         │                                     │
          │  ┌───────────────────────┐                               │
          │  │ ReAnalysis Planner    │                               │
          │  │ (변경사항 파싱 +      │                               │
          │  │  entry_point 결정)    │                               │
          │  └───────────┬───────────┘                               │
          │              │ reanalysis_plan                           │
          │              └───────────────────────────────────────────┘
          │                                     Statistics Agent 재진입
          └────────┬───────────┘
                   ▼
          ┌────────────────┐
          │ Response Node  │
          │ (포맷팅)       │
          └────────┬───────┘
                   │
                   ▼
            사용자에게 응답
            (interrupt → 추가 질문 대기)
                   │
              ┌────┴────┐
              │추가 질문 │──▶ QA Router (루프)
              │종료     │──▶ END
              └─────────┘
```

---

## 7. 외부 시스템 연동 정리

| 외부 시스템 | 연동 방식 | 사용 노드/에이전트 |
| --- | --- | --- |
| **Metrology RDB** | FastAPI → DB 커넥터 | Monitor |
| **사내 RDB (공정/장비/자재)** | FastAPI → DB 커넥터 / MCP: `text_to_sql` | Classify, Statistics Executor, QA Executor |
| **사내 문서 RAG** | Vector DB (Chroma/Milvus 등) | Column Selector, Action Advisor, QA Executor(GENERAL) |
| **MCP 통계 도구** | MCP Protocol | Statistics Executor |
| **MCP text_to_sql** | MCP Protocol | Statistics Executor, QA Executor(DATA) |
| **MCP plot_generator** | MCP Protocol | Reporter Interpreter, QA Executor(DATA) |
| **알림 서비스** | Email/Slack API | Monitor, Report Generator |
| **지식 DB** | FastAPI → DB 저장 | Report Generator |
| **Vue 프론트엔드** | WebSocket / REST API | Report Generator, Response Node |
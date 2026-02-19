# 노드 간 인터페이스 정의서 (Interface Specification)

## 전체 워크플로우

```
┌──────────┐    ┌──────────┐    ┌─────────────┐    ┌──────────────┐
│ Monitor  │───▶│ Classify │───▶│   Column    │───▶│     Tool     │
│          │    │          │    │  Selector   │    │  Selection   │
└──────────┘    └──────────┘    │             │    │     (C)      │
                                 └─────────────┘    └──────────────┘
                                         │                   │
                                         ▼                   ▼
┌──────────┐    ┌──────────┐    ┌─────────────┐    ┌──────────────┐
│  Report  │◀───│  Action  │◀───│ Interpreter │◀───│   Executor   │
│Generator │    │ Advisor  │    │             │    │              │
│          │    │          │    └─────────────┘    └──────────────┘
└──────────┘    └──────────┘
```

---

## 1. Monitor Node

### 개요
PostgreSQL의 metrology 데이터를 능동적으로 감시하여 SPC 위반 또는 이상 현상을 감지

### 감지 대상
- SPC 관리도 위반 (UCL/LCL 초과)
- Western Electric Rules 위반
- Nelson Rules 위반
- 추세 패턴 (연속 증가/감소)
- 주기적 변동 패턴

### 입력 (State 읽기)
- **없음** (시작 노드)

### 출력 (State 쓰기)
| 필드 | 타입 | 설명 |
|------|------|------|
| `trigger` | `Dict` 또는 `None` | SPC 위반 정보 (위반 없으면 None) |

### trigger 구조
```python
{
    "rule_type": str,              # "Western Electric Rule 1" | "Trend Pattern"
    "detection_time": datetime,    # 감지 시각
    "violated_points": List[Tuple[datetime, float]],  # 위반 포인트
    "control_limits": Dict,        # UCL, LCL, center_line
    "sigma_level": float,          # 위반 시그마 레벨
    "severity": str                # "low" | "medium" | "high"
}
```

### 외부 호출
| 시스템 | 용도 | 예상 쿼리 |
|--------|------|----------|
| PostgreSQL | SPC 관리 기준 조회 | `SELECT ucl, lcl, center_line FROM spc_control_limits WHERE parameter = ?` |
| PostgreSQL | 최근 측정 데이터 | `SELECT timestamp, value FROM metrology_data WHERE timestamp > ? AND parameter = ?` |


### 감지 알고리즘 예시
1. **Western Electric Rule 1**: 1 point > 3σ from center line
2. **Western Electric Rule 2**: 2 out of 3 consecutive points > 2σ
3. **Trend Detection**: 7 consecutive points increasing or decreasing
4. **Cyclic Pattern**: 14 points alternating up and down

### 실행 조건 예시
- 주기적 스케줄링 (예: 5분마다)
- 또는 실시간 데이터 스트림 도착 시

### 실행 결과에 따른 분기
- `trigger`가 **있으면** → Classify Node로 진행
- `trigger`가 **None이면** → Workflow 종료 (정상 상태)

### 다음 노드
- **Classify Node** (위반 감지 시만)

---

## 2. Classify Node

### 개요
문제 유형 분류 및 상세 정보 수집

### 입력 (State 읽기)
| 필드 | 필수 | 설명 |
|------|------|------|
| `trigger` | O | Monitor가 생성한 위반 정보 |

### 출력 (State 쓰기)
| 필드 | 타입 | 설명 |
|------|------|------|
| `problem` | `ProblemInfo` | 문제 정의 |

### ProblemInfo 구조
```python
class ProblemInfo(TypedDict):
    problem_code: str              # "SPC-001-UCL"
    description: str               # 자연어 설명
    
    process_name: str              # "Etching"
    equipment_id: str              # "EQP-001"
    lot_number: str                # "LOT-2024-001"
    
    start_time: datetime
    end_time: datetime
    
    affected_parameter: str        # "CD_uniformity"
    statistics: Dict               # min, max, avg, std
    severity: str                  # "low" | "medium" | "high"
```

### 전제조건
- `state["trigger"]`가 존재해야 함

### 외부 호출
| 시스템 | 용도 | 예상 API |
|--------|------|----------|
| PostgreSQL | Lot/Equipment 정보 조회 | `SELECT * FROM lots WHERE ...` |
| PostgreSQL | 측정 파라미터 통계 계산 | `SELECT AVG(), STD() FROM ...` |
| LLM (optional) | 자연어 설명 생성 | Claude API |

### 실행 조건
- `trigger`가 존재할 때 (항상)

### 다음 노드
- **Column Selector Node** (무조건 진행)

---

## 3. Column Selector Node

### 개요
문제 원인 분석을 위한 후보 컬럼 선택

### 입력 (State 읽기)
| 필드 | 필수 | 설명 |
|------|------|------|
| `problem` | O | Classify가 생성한 문제 정의 |

### 출력 (State 쓰기)
| 필드 | 타입 | 설명 |
|------|------|------|
| `columns` | `ColumnSelectionResult` | 선택된 컬럼 정보 |

### ColumnSelectionResult 구조
```python
class ColumnSelectionResult(TypedDict):
    columns: List[Dict]  # column_name, reason, score
    strategy: str        # "correlation_based" | "domain_knowledge"
```

### columns[i] 구조
```python
{
    "column_name": str,        # "gas_flow_rate"
    "reason": str,             # 선택 이유
    "score": float,            # 0.0 ~ 1.0
    "data_summary": Dict       # min, max, avg, std
}
```

### 전제조건
- `state["problem"]`이 존재해야 함

### 외부 호출
| 시스템 | 용도 | 예상 API |
|--------|------|----------|
| PostgreSQL | 후보 컬럼 데이터 조회 | `SELECT column_name FROM ...` |
| PostgreSQL | 상관관계 계산 | `SELECT CORR() ...` |
| LLM | 컬럼 선택 논리 생성 | LLM API |

### 실행 조건
- `problem`이 존재할 때 (항상)

### 다음 노드
- **Tool Selection Node** (무조건 진행)

---

## 4. Tool Selection Node

### 개요
각 컬럼에 적합한 통계 분석 도구 선택

### 입력 (State 읽기)
| 필드 | 필수 | 설명 |
|------|------|------|
| `columns` | O | Column Selector가 선택한 컬럼 |
| `problem` | O | 문제 맥락 참고 |

### 출력 (State 쓰기)
| 필드 | 타입 | 설명 |
|------|------|------|
| `tools` | `ToolSelectionResult` | 도구 할당 정보 |

### ToolSelectionResult 구조
```python
class ToolSelectionResult(TypedDict):
    assignments: List[Dict]  # column_name, tool_name, rationale
```

### assignments[i] 구조
```python
{
    "column_name": str,        # "gas_flow_rate"
    "tool_name": str,          # "t-test" | "correlation" | "anova"
    "mcp_server": str,         # "statistics-mcp"
    "rationale": str           # 선택 이유
}
```

### 전제조건
- `state["columns"]`이 존재해야 함
- `state["problem"]`이 존재해야 함

### 외부 호출
| 시스템 | 용도 | 예상 API |
|--------|------|----------|
| MCP | 사용 가능한 도구 목록 조회 | `list_tools()` |
| LLM | 도구 선택 논리 | Claude API |

### 실행 조건
- `columns`이 존재할 때 (항상)

### 다음 노드
- **Executor Node** (무조건 진행)

---

## 5. Executor Node

### 개요
선택된 도구를 실행하여 통계 분석 수행

### 입력 (State 읽기)
| 필드 | 필수 | 설명 |
|------|------|------|
| `tools` | O | Tool Selection이 선택한 도구 |
| `columns` | O | 분석할 데이터 |

### 출력 (State 쓰기)
| 필드 | 타입 | 설명 |
|------|------|------|
| `execution` | `ExecutionResults` | 실행 결과 |

### ExecutionResults 구조
```python
class ExecutionResults(TypedDict):
    results: List[Dict]  # tool_name, output, status
    summary: Dict        # total, success, failed
```

### results[i] 구조
```python
{
    "execution_id": str,           # "exec_001"
    "tool_name": str,              # "t-test"
    "column_name": str,            # "gas_flow_rate"
    "output": Dict,                # tool의 raw output
    "status": str,                 # "success" | "failed"
    "error": Optional[str],        # 실패 시 에러 메시지
    "duration": float              # 실행 시간 (초)
}
```

### 전제조건
- `state["tools"]`이 존재해야 함
- `state["columns"]`이 존재해야 함

### 외부 호출
| 시스템 | 용도 | 예상 API |
|--------|------|----------|
| MCP Server | 통계 도구 실행 | `call_tool(tool_name, params)` |
| PostgreSQL | 원본 데이터 조회 | `SELECT * FROM ...` |

### 실행 조건
- `tools`이 존재할 때 (항상)

### 다음 노드
- **Interpreter Node** (무조건 진행)

---

## 6. Interpreter Node

### 개요
통계 결과를 자연어로 해석하고 시각화 데이터 생성

### 입력 (State 읽기)
| 필드 | 필수 | 설명 |
|------|------|------|
| `execution` | O | Executor의 분석 결과 |
| `problem` | O | 문제 맥락 참고 |

### 출력 (State 쓰기)
| 필드 | 타입 | 설명 |
|------|------|------|
| `interpretation` | `InterpretationResults` | 해석 결과 |

### InterpretationResults 구조
```python
class InterpretationResults(TypedDict):
    interpretations: List[Dict]  # summary, explanation, chart
    key_insights: List[str]      # 핵심 인사이트
```

### interpretations[i] 구조
```python
{
    "execution_id": str,           # 어떤 실행 결과인지
    "summary": str,                # 한 줄 요약
    "explanation": str,            # 상세 설명
    "chart_type": str,             # "line" | "bar" | "scatter"
    "chart_data": Dict,            # plotly 형식
    "significance": str            # 통계적 유의성 해석
}
```

### 전제조건
- `state["execution"]`이 존재해야 함

### 외부 호출
| 시스템 | 용도 | 예상 API |
|--------|------|----------|
| LLM | 통계 결과 해석 | Claude API |

### 실행 조건
- `execution`이 존재할 때 (항상)

### 다음 노드
- **Action Advisor Node** (무조건 진행)

---

## 7. Action Advisor Node

### 개요
분석 결과 기반 조치 권고 및 관련 문서 검색

### 입력 (State 읽기)
| 필드 | 필수 | 설명 |
|------|------|------|
| `interpretation` | O | Interpreter의 해석 결과 |
| `problem` | O | 문제 정의 |
| `execution` | O | 통계 결과 참고 |

### 출력 (State 쓰기)
| 필드 | 타입 | 설명 |
|------|------|------|
| `recommendation` | `ActionRecommendation` | 조치 권고 |

### ActionRecommendation 구조
```python
class ActionRecommendation(TypedDict):
    actions: List[Dict]       # action, priority, steps, documents
    action_plan: List[str]    # 순서대로 정렬된 action ID
```

### actions[i] 구조
```python
{
    "action_id": str,              # "action_001"
    "type": str,                   # "immediate" | "preventive"
    "priority": str,               # "high" | "medium" | "low"
    "description": str,            # 조치 설명
    "steps": List[str],            # 단계별 실행 방법
    "documents": List[Dict],       # 관련 문서 (RAG 검색 결과)
    "expected_impact": str         # 예상 효과
}
```

### documents[i] 구조
```python
{
    "doc_id": str,                 # 문서 ID
    "title": str,                  # 문서 제목
    "relevance": float,            # 관련도 점수
    "content": str                 # 검색된 내용
}
```

### 전제조건
- `state["interpretation"]`이 존재해야 함
- `state["problem"]`이 존재해야 함

### 외부 호출
| 시스템 | 용도 | 예상 API |
|--------|------|----------|
| ChromaDB | 유사 문서 검색 | `collection.query()` |
| LLM | 조치 권고 생성 | Claude API |

### 실행 조건
- `interpretation`이 존재할 때 (항상)

### 다음 노드
- **Report Generator Node** (무조건 진행)

---

## 8. Report Generator Node

### 개요
전체 분석 결과를 종합하여 최종 리포트 생성

### 입력 (State 읽기)
| 필드 | 필수 | 설명 |
|------|------|------|
| `problem` | O | 문제 정의 |
| `columns` | O | 선택된 컬럼 |
| `tools` | O | 사용된 도구 |
| `execution` | O | 분석 결과 |
| `interpretation` | O | 해석 |
| `recommendation` | O | 권고사항 |

### 출력 (State 쓰기)
| 필드 | 타입 | 설명 |
|------|------|------|
| `report` | `str` | 최종 리포트 (Markdown) |

### report 구조
```markdown
# 품질 분석 리포트

## 1. 문제 정의
- 문제 코드: {problem_code}
- 설명: {description}
...

## 2. 분석 컬럼
...

## 3. 분석 결과
...

## 4. 해석
...

## 5. 권고 조치
...
```

### 전제조건
- 모든 이전 노드의 결과가 존재해야 함

### 외부 호출
| 시스템 | 용도 | 예상 API |
|--------|------|----------|
| (없음) | State 데이터만 사용 | - |

### 실행 조건
- 모든 분석이 완료되었을 때 (항상)

### 다음 노드
- **없음** (종료 노드)

---

## 인터페이스 흐름도

```
State 초기값:
{
  trigger: None,
  problem: None,
  columns: None,
  tools: None,
  execution: None,
  interpretation: None,
  recommendation: None,
  report: None
}

↓ Monitor 실행
{
  trigger: {...},  ← 추가
  ...
}

↓ Classify 실행
{
  trigger: {...},
  problem: {...},  ← 추가
  ...
}

↓ Column Selector 실행
{
  ...
  columns: {...},  ← 추가
  ...
}

↓ Tool Selection 실행
{
  ...
  tools: {...},    ← 추가
  ...
}

↓ Executor 실행
{
  ...
  execution: {...}, ← 추가
  ...
}

↓ Interpreter 실행
{
  ...
  interpretation: {...}, ← 추가
  ...
}

↓ Action Advisor 실행
{
  ...
  recommendation: {...}, ← 추가
  ...
}

↓ Report Generator 실행
{
  ...
  report: "..."  ← 추가
}
```

---

## 개발 가이드

### 각 노드 개발 시 체크 방법 예시

1. **입력 검증**
   ```python
   def my_node(state: AnalysisState) -> AnalysisState:
       # 1. 필수 필드 확인
       if state.get("required_field") is None:
           raise ValueError("required_field is missing")
       
       # 2. 데이터 타입 확인
       assert isinstance(state["required_field"], dict)
   ```

2. **출력 생성**
   ```python
   # 1. 결과 타입 맞추기
   result: MyNodeOutput = {
       "field1": value1,
       "field2": value2
   }
   
   # 2. State 업데이트
   return {**state, "my_output": result}
   ```

3. **에러 처리**
   ```python
   try:
       result = external_api_call()
   except Exception as e:
       # 에러를 State에 기록
       return {
           **state,
           "my_output": {"status": "failed", "error": str(e)}
       }
   ```

### 독립 테스트 방법

```python
# test_my_node.py
from schemas import AnalysisState
from nodes.my_node import my_node

def test_my_node():
    # Mock State 생성
    mock_state: AnalysisState = {
        "trigger": {...},  # 필요한 입력만
        "problem": None,
        # ... 나머지는 None
    }
    
    # 노드 실행
    result = my_node(mock_state)
    
    # 출력 검증
    assert result["my_output"] is not None
    assert result["my_output"]["field1"] == expected_value
```


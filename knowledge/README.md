# Knowledge Assets

RAG 시스템에 탑재될 5대 지식 자산 PDF 보관 폴더.

`docs/` 아래에 PDF를 추가한 뒤 인덱서를 실행하면 ChromaDB에 적재된다.

```
docker compose exec be python -m src.rag.indexer
```

## 문서 목록

| 파일명 | doc_type | 내용 | 활용처 |
|--------|----------|------|--------|
| `Fab_Equipment_Hierarchy.pdf` | SPEC | 장비-챔버-부품 소속 관계도 | 문제 범위 특정 |
| `Part_Lifecycle_Spec.pdf` | SPEC | 부품별 교체 주기 및 가격 | 교체 시기 판단 |
| `Tech_Note_APC_Valve.pdf` | TECH_NOTE | 압력-밸브 각도 상관관계 | 이상 감지 근거 |
| `Issue_Report_20240520.pdf` | REPORT | 2024-05-20 O-ring 사고 이력 | Action Advisor / QA |
| `OCAP_Etch_Valve_Drift.pdf` | MANUAL | Valve Drift 표준 대응 절차 | 조치 방안 제시 |

## 메타데이터 스키마

```python
{
    "source":        "파일명",
    "doc_type":      "MANUAL" | "REPORT" | "SPEC" | "TECH_NOTE",
    "equipment":     "장비명1,장비명2",   # 콤마 구분 문자열
    "component":     "부품명1,부품명2",   # 콤마 구분 문자열
    "incident_date": "YYYY-MM-DD",        # REPORT인 경우만
}
```

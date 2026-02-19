
import time
import pandas as pd
import numpy as np
from src.utils.validators import validate_data

async def control_chart_analysis(
    target: str,
    features: list[str], # 선택사항 (그룹핑 변수 등)
    data: list[dict],
    options: dict | None = None,
) -> dict:
    """
    관리도(Control Chart) 데이터를 생성하고 Cp, Cpk를 계산합니다.
    기본적으로 I-MR 관리도(Individual) 개념을 사용합니다.
    
    Args:
        target: 측정값 컬럼
        options: {"usl": float, "lsl": float, "sigma": int (default 3)}
    """
    start = time.time()
    options = options or {}
    sigma_lvl = options.get("sigma", 3)
    usl = options.get("usl")
    lsl = options.get("lsl")
    
    is_valid, error, df = validate_data(data, [target])
    if not is_valid:
        return {"tool_name": "control_chart_analysis", "error": error, "execution_time_ms": 0}
        
    try:
        # 데이터 준비
        values = pd.to_numeric(df[target], errors='coerce').dropna().values
        
        if len(values) < 2:
            return {"tool_name": "control_chart_analysis", "error": "Not enough data points", "execution_time_ms": 0}

        # 관리한계 계산 (CL: Mean, UCL, LCL)
        mean_val = np.mean(values)
        std_val = np.std(values, ddof=1) # Sample Std Dev
        
        ucl = mean_val + sigma_lvl * std_val
        lcl = mean_val - sigma_lvl * std_val
        
        # 위반 포인트 식별
        violations = []
        for i, val in enumerate(values):
            if val > ucl or val < lcl:
                violations.append({"index": int(i), "value": float(val), "type": "OOC"})
                
        # 공정능력지수 (Cp, Cpk)
        cp, cpk = None, None
        if usl is not None and lsl is not None:
            # Cp = (USL - LSL) / 6sigma
            cp = (usl - lsl) / (6 * std_val) if std_val > 0 else 0
            
            # Cpk = min((USL - mean) / 3sigma, (mean - LSL) / 3sigma)
            cpu = (usl - mean_val) / (3 * std_val) if std_val > 0 else 0
            cpl = (mean_val - lsl) / (3 * std_val) if std_val > 0 else 0
            cpk = min(cpu, cpl)
            
        results = {
            "mean_cl": float(mean_val),
            "std_dev": float(std_val),
            "ucl": float(ucl),
            "lcl": float(lcl),
            "violations": violations,
            "violation_count": len(violations),
            "process_capability": {
                "Cp": float(cp) if cp is not None else None,
                "Cpk": float(cpk) if cpk is not None else None,
                "USL": usl,
                "LSL": lsl
            }
        }

    except Exception as e:
        return {"tool_name": "control_chart_analysis", "error": str(e), "execution_time_ms": int((time.time() - start) * 1000)}

    return {
        "tool_name": "control_chart_analysis",
        "results": results,
        "execution_time_ms": int((time.time() - start) * 1000)
    }

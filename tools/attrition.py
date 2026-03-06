import pandas as pd

DEFAULT_RISK_THRESHOLD = 15.0  # percent


def compute_attrition_rate(df: pd.DataFrame, segment: dict | None = None) -> float:
    result = df.copy()
    if segment:
        for col, val in segment.items():
            if col in result.columns and result[col].dtype == object:
                result = result[result[col].str.lower() == str(val).lower()]
    if "attrition" not in result.columns or result.empty:
        return 0.0
    return round(float(result["attrition"].mean()) * 100, 2)


def segment_workforce(df: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    valid_dims = [d for d in dimensions if d in df.columns]
    if not valid_dims or "attrition" not in df.columns:
        return df
    return df.groupby(valid_dims)["attrition"].mean().reset_index()


def flag_risk(rate: float, threshold: float = DEFAULT_RISK_THRESHOLD) -> str:
    if rate >= threshold * 1.3:
        return "HIGH"
    elif rate >= threshold:
        return "MEDIUM"
    return "LOW"

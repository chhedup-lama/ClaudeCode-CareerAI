import numpy as np
import pandas as pd


def compute_benchmark(df: pd.DataFrame, metric: str, percentile: float = 50) -> float:
    if metric not in df.columns:
        raise ValueError(f"Column '{metric}' not found in dataset")
    return round(float(np.percentile(df[metric].dropna(), percentile)), 2)


def detect_trend(df: pd.DataFrame, metric: str, year_col: str = "year") -> dict:
    if metric not in df.columns or year_col not in df.columns:
        return {"yoy_change_pct": 0.0, "direction": "stable"}

    yearly = df.groupby(year_col)[metric].mean().sort_index()
    if len(yearly) < 2:
        return {"yoy_change_pct": 0.0, "direction": "stable"}

    latest, previous = yearly.iloc[-1], yearly.iloc[-2]
    yoy = round(((latest - previous) / previous) * 100, 2) if previous != 0 else 0.0
    direction = "increasing" if yoy > 1 else ("decreasing" if yoy < -1 else "stable")
    return {"yoy_change_pct": yoy, "direction": direction}

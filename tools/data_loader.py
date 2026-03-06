import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_csv(file_name: str) -> pd.DataFrame:
    path = DATA_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path)


def filter_dataset(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    result = df.copy()
    for col, value in filters.items():
        if col not in result.columns:
            continue
        if result[col].dtype == object:
            result = result[result[col].str.lower() == str(value).lower()]
        else:
            result = result[result[col] == value]
    return result


def check_data_availability(files: list[str]) -> dict[str, bool]:
    return {f: (DATA_DIR / f).exists() for f in files}

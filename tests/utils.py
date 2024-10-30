import pandas as pd


def modify_date_columns(df: pd.DataFrame, date_columns: list) -> pd.DataFrame:
    for col in date_columns:
        df[col] = pd.to_datetime(df[col])
    return df

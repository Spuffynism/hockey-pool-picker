import json
from pathlib import Path

import pandas as pd


def read_to_df(path: str) -> pd.DataFrame:
    base_dir = Path(__file__).parent.parent.parent
    print(base_dir / 'data' / Path(path))
    return pd.read_json(base_dir / 'data' / Path(path), lines=True)

def write(path: str, records: list[dict]):
    with open('data' / Path(path), "w") as file:
        for row in records:
            # default=str to handle dates
            file.write(json.dumps(row, separators=(',',':'), ensure_ascii=False, default=str) + "\n")
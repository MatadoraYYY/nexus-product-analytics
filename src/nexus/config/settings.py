import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    data_dir: str = os.getenv("DATA_DIR", "data")
    duckdb_path: str = os.getenv("DUCKDB_PATH", "data/nexus.duckdb")
    gross_margin: float = float(os.getenv("GROSS_MARGIN", "0.80"))
    seed: int = 42

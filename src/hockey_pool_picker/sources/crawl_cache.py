from pathlib import Path

import requests_cache

base_dir = Path(__file__).parent.parent.parent.parent

print(base_dir)

session = requests_cache.CachedSession(base_dir / "data" / "cache" / "requests")

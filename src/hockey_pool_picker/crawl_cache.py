from datetime import timedelta

import requests_cache

session = requests_cache.CachedSession("requests_cache", expire_after=timedelta(weeks=52))
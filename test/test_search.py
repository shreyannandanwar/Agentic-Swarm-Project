# test/test_search.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.search import search_web

results = search_web(
    "What is LangGraph?",
    max_results=3
)

for result in results:
    print("-" * 50)
    print(result["title"])
    print(result["url"])
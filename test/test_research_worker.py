import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.research_worker import research_subquestion

result = research_subquestion(
    "What are the main features of LangGraph?"
)

print("\n")
print("=" * 80)
print(result["answer"])
# test/test_llm.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.llm import generate

response = generate(
    "What is LangGraph?"
)

print(response)
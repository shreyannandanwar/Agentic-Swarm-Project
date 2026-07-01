# test_planner.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.planner import generate_subquestions

query = "Should I learn LangGraph or CrewAI?"

questions = generate_subquestions(query)

for q in questions:
    print(q)
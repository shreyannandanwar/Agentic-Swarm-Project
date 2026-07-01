# app/orchestrator.py
import asyncio

from app.planner import generate_subquestions
from app.research_worker import research_subquestion
from app.analyst import analyze_findings


async def run_research(query: str):
    print("\n📋 Generating research plan...")
    questions = generate_subquestions(query)

    if not questions:
        raise RuntimeError("Planner failed to generate research questions.")

    print(f"\nPlanned {len(questions)} questions:\n")
    for i, q in enumerate(questions, start=1):
        print(f"{i}. {q}")

    print("\n🚀 Launching research workers...\n")
    tasks = [research_subquestion(q) for q in questions]
    worker_outputs = await asyncio.gather(*tasks, return_exceptions=True)

    successful_workers = []
    for i, w in enumerate(worker_outputs):
        if isinstance(w, Exception):
            print(f"❌ Worker {i+1} failed: {w}")
            continue
        successful_workers.append(w)

    if not successful_workers:
        raise RuntimeError("All research workers failed.")

    print(f"\n✅ {len(successful_workers)} workers completed successfully.")
    print(f"   Total claims: {sum(len(w.claims) for w in successful_workers)}")

    print("\n🧠 Running Analyst Agent...\n")
    finding = analyze_findings(
        question=query,        # ← FIXED: was 'query', should be 'question'
        workers=successful_workers
    )

    print(f"✅ Analyst completed (confidence={finding.overall_confidence:.2f})")
    print(f"   Merged claims: {len(finding.claims)}")
    print(f"   Conflicts: {len(finding.conflicts)}")

    return [finding]
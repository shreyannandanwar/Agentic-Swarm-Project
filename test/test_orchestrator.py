# test/test_orchestrator.py
import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.orchestrator import run_research

async def test():
    results = await run_research(
        "Should I learn LangGraph or CrewAI?"
    )

    for item in results:
        print("\n")
        print("=" * 80)
        print("QUESTION:", item.question)
        print("CONFIDENCE:", item.overall_confidence)
        print("=" * 80)
        print("SUMMARY:", item.summary)
        print("\nCLAIMS:")
        for claim in item.claims:
            print(f"  - {claim.statement} (Sources: {claim.sources})")
        if item.conflicts:
            print("\nCONFLICTS:")
            for conflict in item.conflicts:
                print(f"  - {conflict.topic}: {conflict.explanation}")

if __name__ == "__main__":
    asyncio.run(test())

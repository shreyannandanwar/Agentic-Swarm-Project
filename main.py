#main.py
import sys
from app.orchestrator import run_research
from app.report_generator import generate_report
import asyncio
import time

def main():
    start = time.perf_counter()
    if len(sys.argv) < 2:
        print('Usage: python main.py "your question"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print("\n\n\n===================================================================\n\n\n")
    # Phase 1: Plan + Research
    print(f"\n🔬 Researching: {query}")
    findings = asyncio.run(run_research(query))

    # Phase 2: Synthesize
    print("\n📝 Generating final report...")
    report = generate_report(query, findings)
    end = time.perf_counter()
    print(f"\n⏱️  Report generated in {end - start:.2f} seconds")

    # Phase 3: Output
    print("\n" + "=" * 80)
    print("RESEARCH REPORT")
    print("=" * 80)
    print(report)
    print("=" * 80)

if __name__ == "__main__":
    main()
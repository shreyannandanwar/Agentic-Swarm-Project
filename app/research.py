#research.py
from app.llm import generate
from app.search import search_web


def build_context(results):
    context = []

    for idx, result in enumerate(results, start=1):
        title = result.get("title", "")
        url = result.get("url", "")
        content = result.get("content", "")[:500]

        context.append(
            f"""
SOURCE {idx}
TITLE: {title}
URL: {url}

CONTENT:
{content}
"""
        )

    return "\n".join(context)


def research(query: str):
    search_results = search_web(query)

    source_context = build_context(search_results)

    prompt = f"""
You are a research assistant.

Question:
{query}

Sources:
{source_context}

Instructions:

1. Use ONLY the provided sources.
2. Write a concise research report.
3. Cite source numbers like [1], [2].
4. If sources disagree, mention it.
5. Do not invent facts.

Output Format:

# Summary

...

# Key Findings

- ...
- ...

# Sources

[1] ...
[2] ...
"""

    report = generate(prompt)

    return {
        "query": query,
        "report": report,
        "sources": search_results,
    }
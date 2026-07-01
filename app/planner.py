#planner.py
from app.llm import generate
import re


def generate_subquestions(query: str):

    prompt = f"""
You are a research planner.

Your job is NOT to answer the question.

Your ONLY job is to break a complex comparative research question into EXACTLY 5 decision-oriented sub-questions.
Each sub-question must target one of these specific domains to help a user decide which framework/tool to learn or adopt:
1. Core Architecture: How do their architectures, programming models, and core execution flows compare?
2. Learning Curve: What are the setup requirements, documentation quality, and learning curve differences?
3. Production Readiness: How do they handle production concerns such as state management, persistence, scalability, and deployment?
4. Community & Ecosystem: What are their GitHub activity levels, community support, and ecosystem sizes?
5. Limitations & Anti-patterns: What are the key limitations, and in what scenarios or when should a developer NOT use each framework/tool?

Original Question:
{query}

Rules:
- Return EXACTLY 5 questions.
- One question per line.
- Number them 1-5.
- Do not explain.
- Do not answer.
- Do not include any extra text.

Example format:
1. [Question about core architecture and design patterns]
2. [Question about setup complexity, docs, and learning curve]
3. [Question about production state management, persistence, and scalability]
4. [Question about community size, activity, and ecosystems]
5. [Question about limitations and scenarios when not to use them]
"""

    response = generate(prompt, model="fast")

    print("\n===== Planner Raw Output =====")
    print(response)
    print("==============================\n")

    questions = []

    for line in response.splitlines():

        line = line.strip()

        if not line:
            continue

        match = re.match(r"^\d+[\.\)]\s*(.+)", line)

        if match:
            questions.append(match.group(1).strip())

    return questions[:5]




#prompt1 = f"""
# Break the following research question into 5 focused
# research subquestions.

# Question:
# {query}

# Return ONLY a numbered list.

# Example:

# 1. ...
# 2. ...
# 3. ...
# 4. ...
# 5. ...
# """


# f"""Break this research question into 5 focused, verifiable subquestions.

#         CRITICAL RULES:
#         1. Each subquestion must be answerable with specific facts, not opinions
#         2. Prefer questions about: API features, performance benchmarks, version numbers, GitHub metrics, architectural patterns
#         3. AVOID questions about: "ease of use," "learning curves," "productivity," "efficiency" — these produce opinionated blog posts, not evidence
#         4. Each subquestion should target a different source type (docs, GitHub, benchmarks, architecture)

#         Question: {query}

#         Return ONLY a numbered list.
#         """


# f"""Answer using ONLY the provided sources. Be a forensic analyst, not a summarizer.

#         RULES:
#         1. Every claim must have a source citation [1], [2], etc.
#         2. Prefer QUANTIFIED facts: "X has Y stars" not "X is popular"
#         3. Include SPECIFIC API names, version numbers, or configuration options when mentioned
#         4. If a source makes a comparative claim ("faster than," "better than"), note the baseline
#         5. If sources CONFLICT, state the conflict explicitly: "Source [1] claims X, but Source [2] claims Y"
#         6. If no specific facts are found, state: "No quantified data found in sources"

#         Question: {query}

#         Sources:
        

#         Format:
#         SUMMARY: (1 sentence)
#         FACTS:
#         - Specific fact with citation [1]
#         - Specific fact with citation [2]
#         CONFLICTS: (list any, or "None detected")
#         DATA GAPS: (what specific data was missing?)
#         """

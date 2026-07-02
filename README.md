# Agentic Swarm Project

An autonomous, multi-agent research assistant that breaks down complex comparative questions, searches the web asynchronously, extracts structured evidence, and synthesizes a professional decision report.

Powered entirely by local LLMs via Ollama, this project avoids external API costs while maintaining a robust pipeline with semantic deduplication, source-tier weighting, and conflict detection.

## Key Features

 **Multi-Agent Orchestration:** A pipeline consisting of a Planner, async Research Workers, an Analyst, and a Report Generator. \
 **Local-First:** 100% powered by local models (Ollama). No OpenAI/Anthropic API keys required. \
 **Asynchronous Execution:** Research workers run concurrently using asyncio for rapid information gathering. \
 **Semantic Deduplication:** Uses Jaccard similarity to merge overlapping claims across different workers without relying on heavy vector embeddings. \
 **Tier-Weighted Confidence Scoring:** Evaluates claims based on source authority (Official, Established, Low), cross-verification across multiple sources, and quantification bonuses. \
 **Conflict Detection:** Distinguishes between agreements, duplicates, and actual contradictions (using negation heuristics).

## Architecture Pipeline

The system operates in four distinct phases:

Generates 5 Sub-Questions
Search Web via Tavily
Extract Claims & Evidence
Worker Outputs
Merge, Conflict Detect, Score
User Query
Planner Agent - Fast Model
Async Research Workers - Smart Model
Web
Analyst Agent - Smart Model
Structured Findings
Report Generator - Deep Model

Final Decision Report - 
**Planner:** Breaks the user's prompt into exactly 5 decision-oriented sub-questions (Architecture, Learning Curve, Production Readiness, Community, Limitations).
**Research Workers:** Launch concurrently per sub-question. They search the web, build context, and extract strict JSON facts mapped to source URLs.
**Analyst:** Merges claims semantically, detects contradictions, calculates overall confidence based on source tiers, and generates a summary.
**Report Generator:** Synthesizes the structured findings into a final markdown report with an executive summary, key findings, analysis, and actionable recommendations.
## 🛠️ Prerequisites

 Python 3.13
 Ollama installed and running on your machine
 Tavily API Key (for web search capabilities)
Required Ollama Models

Based on the project configuration, ensure you have pulled the following models:

```bash
ollama pull llama3.1:latest
ollama pull qwen3.5:latest
ollama pull gemma3:12b-it-qat
ollama pull mistral-small:latest
```
*(Note: You can map these models to the fast, smart, and deep roles in your app/llm.py configuration).*

## ⚙️ Installation & Setup

Clone the repository:
```bash
git clone https://github.com/your-username/agentic-swarm-project.git
cd agentic-swarm-project
```

Create and activate a virtual environment:
```bash
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

**Configure Environment Variables:** Create a .env file in the root directory and add your Tavily API key:
```bash
TAVILY_API_KEY=your_tavily_api_key_here
```
💻 Usage

Run the script from the command line, passing your research question as an argument:

```bash
python main.py "React vs Vue for enterprise applications"
```

## Example Output
```bash
🔬 Researching: React vs Vue for enterprise applications

📋 Generating research plan...

Planner Raw Output-
1. How do React and Vue's core architectures, programming models, and execution flows differ...
2. What are the setup requirements, documentation quality, and learning curve differences...
3. How do React and Vue handle production concerns such as state management, data persistence...
4. What are the GitHub activity levels, community support, and ecosystem sizes of React and Vue...
5. What are the key limitations and anti-patterns of each framework, and in what scenarios...

Planned 5 questions:
[... 5 questions output ...]

🚀 Launching research workers...

🔍 How do React and Vue's core architectures...
🔍 What are the setup requirements...
🔍 How do React and Vue handle production concerns...
🔍 What are the GitHub activity levels...
🔍 What are the key limitations and anti-patterns...
   📊 Source tiers: {'ESTABLISHED': 3}
   📊 Source tiers: {'ESTABLISHED': 1, 'LOW': 2}
   📊 Source tiers: {'LOW': 3}
   📊 Source tiers: {'ESTABLISHED': 2, 'LOW': 1}
   📊 Source tiers: {'ESTABLISHED': 2, 'LOW': 1}

✅ 5 workers completed successfully.
   Total claims: 24

🧠 Running Analyst Agent...

✅ Analyst completed (confidence=0.43)
   Merged claims: 24
   Conflicts: 0

📝 Generating final report...

⏱️  Report generated in 537.78 seconds
```

## RESEARCH REPORT

### Executive Summary

For enterprise applications, **React is generally the recommended choice**, particularly for larger organizations and complex projects requiring high scalability. While Vue offers a gentler learning curve and faster development speed, React's broader community support, established ecosystem, and proven track record in handling large-scale applications outweigh these advantages. However, if rapid prototyping and maintainability are paramount within a medium-sized enterprise, Vue presents a viable alternative.

### Key Findings

*   **Component Structure:** React uses JSX for UI component definition and primarily utilizes Functional components [1, 2]. Vue offers two approaches: Composition API and Options API [2].
*   **Data Binding:** Vue provides two-way data binding, while React enforces unidirectional data flow [1].
[... truncated for brevity ...]

### Recommendation

**For new enterprise application development, prioritize React.** Invest in training resources to address its steeper learning curve. Leverage its extensive ecosystem and community support for faster problem-solving and access to pre-built components. If rapid prototyping or a smaller team with limited JavaScript experience is a key constraint within a medium-sized organization, Vue should be considered as an alternative, but carefully evaluate the long-term scalability implications.

### 🗺️ Roadmap

This is V1 of the Agentic Swarm. Future updates will focus on deeper reasoning and architectural improvements:

V2 Goals:

 Atomic Claim Extraction: Moving away from summarized facts to granular, atomic claims.
 Source-Aware Confidence: Deeper integration of evidence quality and provenance into the scoring logic.
 Advanced Contradiction Detection: True differentiation between agreement, contradiction, and complementary information.
 Evidence-Backed Recommendations: The Analyst agent will generate the final recommendations, rather than the Report Generator.
 Pure Renderer: The Report Generator will become a strict formatting component, removing reasoning from the synthesis stage.
V3+ Goals:

 Migration to LangGraph for more complex state management and agent routing.
 
### 🤝 Contributing

This is currently a V1 release. If you have suggestions, feature requests, or bug fixes, please feel free to:

Fork the repository \
Create a feature branch (git checkout -b feature/AmazingFeature) \
Commit your changes (git commit -m 'Add some AmazingFeature') \
Open a Pull Request
### 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

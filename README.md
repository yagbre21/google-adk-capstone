# Agentic Job Search Recommender

Your resume argues with itself. Two AI agents debate your level, reach consensus, then find jobs you'd actually take. Under 5 minutes.

## The Problem

Job boards treat your resume as a bag of keywords. They match "Python" to "Python" and call it a day. The real problem isn't search. It's calibration.

## The Solution

A multi-agent system that creates artificial tension through deliberation:

```
Resume → Parser → Classifier → [Conservative ║ Optimistic] → Consensus
                                           ↓
            [Exact ║ Level Up] then [Stretch ║ Trajectory] → Validator → Output
```

**Seven stages. Three model tiers. Four job recommendations. One argument.**

## 4-Tier Job Output

| Tier | What It Means |
|------|---------------|
| Exact Match | You could land this next week |
| Level Up | Your next promotion, externally |
| Stretch | Ambitious but possible |
| Trajectory | Where your career wants to go |

## Tech Stack

- Google ADK (Agent Development Kit)
- Gemini 2.5 Flash, Pro, and Flash-Lite
- Google Search Grounding
- Python 3.10+

## ADK Concepts Demonstrated

Multi-agent orchestration, custom tools, built-in tools, A2A Protocol, Sessions, Memory, and Human-in-the-loop. The requirement was 3. This demonstrates 7.

## Quick Start

```bash
# Install dependencies
pip install google-adk>=1.19.0 google-genai pypdf2 python-docx

# Set API key
export GOOGLE_API_KEY=your_key_here

# Run the notebook
jupyter notebook Submission/agentic_job_search.ipynb
```

## Competition

Built for the [Kaggle Agents Intensive Capstone Project](https://www.kaggle.com/competitions/agents-intensive-capstone-project) (November 2025).

**Track:** Concierge Agents

## License

CC-BY-SA 4.0

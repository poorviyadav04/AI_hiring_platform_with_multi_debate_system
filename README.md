# HireScope AI

> **AI-Powered Hiring Platform with Multi-Agent Debate & Semantic Skill Matching**

A full-stack hiring intelligence platform that uses **multi-agent debate**, **semantic skill matching**, and **explainable scoring** to evaluate candidates. Upload resumes, paste job descriptions, and get transparent, data-driven hiring decisions.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What This System Does

**For Candidates** -- Upload your resume + paste a job description to get:
- An overall fit score with component breakdown (Skills, Experience, Education)
- Gap analysis showing exactly what you're missing and how critical each gap is
- "What-if" counterfactuals ("If you learned Docker, your score would increase by +6 pts")
- A personalized learning roadmap with resources and timelines

**For Hiring Teams** -- Upload multiple resumes to get:
- Ranked candidates with transparent scores
- Multi-agent debate: 4 AI agents (Evaluator, Advocate, Skeptic, Moderator) argue over each candidate like a real hiring committee
- GitHub profile verification for claimed skills
- Exportable, auditable decision trails

---

## Key Features

### Semantic Skill Matching (Embedding-Based)
Traditional systems use exact string matching -- if the JD says "Machine Learning" and your resume says "PyTorch", it's a zero match. This system uses **sentence-transformer embeddings** (`all-MiniLM-L6-v2`) to understand that PyTorch *is* Machine Learning.

| JD Requirement | Resume Skill | Similarity | Match |
|:---|:---|:---|:---|
| Machine Learning | Scikit-learn | 0.71 | Full |
| Cloud AI Services | AWS | 0.60 | Partial |
| Backend Development | FastAPI | 0.65 | Partial |
| Microfinance | PyTorch | 0.46 | No match |

Cross-domain mismatches are correctly rejected -- an ML engineer applying for a finance role scores low on skills, not 90%.

### Multi-Agent Debate System
Four specialized agents evaluate each candidate:

| Agent | Role | What It Does |
|:---|:---|:---|
| **Evaluator** | Objective scorer | Runs deterministic scoring -- no hallucination |
| **Advocate** | Makes the case FOR | Highlights strengths, cites similar successful hires |
| **Skeptic** | Identifies risks | Flags concerns, gaps, and retention risks |
| **Moderator** | Final decision | Synthesizes the debate, checks consistency with past decisions |

### Explainable Scoring Engine
Every score is transparent and auditable:

```
Overall Score = Skills (50%) + Experience (35%) + Education (15%)
```

- **Skills:** Semantic embedding match against required + preferred skills
- **Experience:** Gap analysis with level multipliers (junior/mid/senior)
- **Education:** Hierarchy-based comparison (High School to PhD)

No black boxes. Every point is traceable to a specific component.

### Counterfactual Explanations
Shows candidates exactly what would improve their score:

```
"If you added Docker, your score would increase from 65 to 71 (+6 pts)"
"Strengthen Cloud AI Services (currently 60% covered via AWS): +3 pts"
```

### Gap Analysis & Learning Roadmap
Identifies skill, experience, and education gaps with severity levels (critical/moderate/minor) and generates a personalized learning roadmap with:
- Specific courses and platforms
- Estimated weeks to proficiency
- Impact on score if the gap is closed

---

## Tech Stack

| Layer | Technology | Purpose |
|:---|:---|:---|
| **Frontend** | Next.js 16, React 19, Tailwind CSS | Candidate & hiring team UI |
| **Backend API** | FastAPI, Uvicorn | REST endpoints with async support |
| **LLM** | Google Gemini / Groq (configurable) | Resume parsing, JD parsing, roadmap generation |
| **Skill Matching** | sentence-transformers (all-MiniLM-L6-v2) | Semantic similarity between skills |
| **Scoring** | Custom Python (deterministic) | Zero-hallucination scoring engine |
| **Agents** | Custom multi-agent framework | Debate-based candidate evaluation |
| **Data Validation** | Pydantic v2 | Type-safe models with field validators |
| **PDF Parsing** | pypdf | Resume text extraction |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Gemini API key ([get one free](https://aistudio.google.com/apikey)) or Groq API key ([get one free](https://console.groq.com/keys))

### Setup

```bash
# Clone
git clone <repository-url>
cd hiring-system

# Backend
cd backend
pip install -e .
cp .env.example .env  # Add your API keys

# Frontend
cd ../frontend
npm install
```

### Run

**Terminal 1 -- Backend:**
```bash
cd backend
uvicorn api.main:app --reload --port 8001
```

**Terminal 2 -- Frontend:**
```bash
cd frontend
npm run dev
```

- **App:** http://localhost:3000
- **API Docs:** http://localhost:8001/docs

---

## API Endpoints

| Endpoint | Method | Description |
|:---|:---|:---|
| `/api/candidate/analyze` | POST | Upload resume + JD, get full candidate analysis |
| `/api/hiring/evaluate` | POST | Upload multiple resumes + JD, get ranked evaluations |
| `/api/github/verify` | POST | Verify a GitHub profile against claimed skills |
| `/api/health` | GET | Health check |

---

## Project Structure

```
hiring-system/
├── backend/
│   ├── api/                          # FastAPI routes & dependency injection
│   │   ├── main.py                   # App entry, CORS, lifespan (model preload)
│   │   ├── dependencies.py           # Singletons: LLM, SkillMatcher
│   │   └── routers/                  # candidate, hiring, github, health
│   ├── src/hiring_engine/
│   │   ├── scoring/
│   │   │   ├── skill_matcher.py      # Semantic embedding matcher
│   │   │   ├── skills.py             # Skill scoring (semantic + exact fallback)
│   │   │   ├── overall.py            # Weighted overall score
│   │   │   ├── experience.py         # Experience gap scoring
│   │   │   ├── education.py          # Education hierarchy scoring
│   │   │   └── gap_analysis.py       # Gap detection + roadmap generation
│   │   ├── counterfactuals/
│   │   │   └── generator.py          # "What-if" scenario engine
│   │   ├── parsers/
│   │   │   ├── resume_parser.py      # PDF → structured profile (LLM)
│   │   │   └── jd_parser.py          # JD text → structured requirements (LLM)
│   │   ├── agents/                   # Evaluator, Advocate, Skeptic, Moderator
│   │   ├── schemas/                  # Pydantic models
│   │   └── llm/                      # Gemini & Groq clients
│   └── .env                          # API keys
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js pages (candidate, hiring)
│   │   ├── components/               # ScoreCard, GapAnalysis, Roadmap, etc.
│   │   └── lib/                      # API client, types
│   └── .env.local                    # Backend URL config
└── README.md
```

---

## How Scoring Works

### Skill Matching Pipeline
```
Resume Skills ──→ Normalize (alias map) ──→ Embed (all-MiniLM-L6-v2)
                                                      │
JD Skills ──────→ Normalize (alias map) ──→ Embed ────┤
                                                      ▼
                                            Cosine Similarity Matrix
                                                      │
                                            Greedy 1:1 Assignment
                                                      │
                                    ┌─────────────────┼─────────────────┐
                                    ▼                 ▼                 ▼
                              >= 0.70            0.58-0.69          < 0.58
                             Full Match       Partial Match        No Match
                             (score=1.0)    (score=similarity)    (score=0)
```

### Alias Normalization (built-in, ~80 entries)
Handles common abbreviations before embedding:
```
"JS" → "JavaScript"    "ML" → "Machine Learning"    "K8s" → "Kubernetes"
"AWS" → "Amazon Web Services"    "CI/CD" → "Continuous Integration..."
```

### Experience Scoring
- Perfect match (within 0.5 years): 100
- Overqualified 2x+: 90 (retention risk flag)
- Underqualified: penalty of 15-20 pts per year gap
- Level multiplier: junior=1.1, mid=1.0, senior=0.95, staff=0.9

### Education Scoring
Hierarchy: High School → Associate → Bootcamp → Bachelor → Master → PhD

Exact match = 100, one above = 95, below = 30-85 based on gap.

---

## Performance

| Metric | Value |
|:---|:---|
| Embedding model load | ~5s (once at startup) |
| Skill matching (20 skills) | ~30ms |
| Full candidate analysis | ~5-8s (includes LLM calls) |
| Hiring team eval (2 candidates) | ~15-20s |

---

## Configuration

### Environment Variables (backend/.env)

| Variable | Required | Description |
|:---|:---|:---|
| `GEMINI_API_KEY` | Yes* | Google Gemini API key |
| `GROQ_API_KEY` | Yes* | Groq API key (*one of Gemini/Groq required) |
| `GITHUB_TOKEN` | No | GitHub token for higher rate limits (60 → 5000 req/hr) |
| `CORS_ORIGINS` | No | Allowed origins (default: localhost:3000) |

### Skill Matcher Tuning (skill_matcher.py)

| Constant | Default | Purpose |
|:---|:---|:---|
| `FULL_MATCH_THRESHOLD` | 0.70 | Similarity >= this counts as full match |
| `PARTIAL_MATCH_THRESHOLD` | 0.58 | Similarity >= this counts as partial match |
| `MODEL_NAME` | all-MiniLM-L6-v2 | Sentence transformer model |

---

## License

MIT

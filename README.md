# 🛡️ PlagGuard

**Production-grade Plagiarism Detection, AI Text Detection & Text Humanization Platform**

> Paste any text → get an instant plagiarism report, AI-probability score, and a one-click humanized rewrite that passes detection.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![React](https://img.shields.io/badge/react-18-61dafb)

---

## ✨ Features

| Capability | What It Does |
|---|---|
| **Plagiarism Detection** | Sentence-level semantic similarity using sentence-transformers + n-gram overlap |
| **AI Text Detection** | Multi-signal analysis — perplexity, burstiness, vocabulary diversity, connector density |
| **Text Humanization** | LLM-powered rewriting (OpenAI / Anthropic) with 3 intensity levels |
| **Web Source Check** | Optional Google Custom Search cross-referencing |
| **Full Pipeline** | Detect → Humanize → Re-detect in one click, with before/after comparison |
| **Report Generation** | Beautiful HTML reports with risk scores, flagged sentences, and statistics |
| **Self-Plagiarism** | Detects repeated/recycled sentences within the same document |
| **Production Middleware** | Rate limiting, request size caps, CORS, structured logging |

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│                   React Frontend                 │
│  Tabs: Detect │ Humanize │ Full Pipeline         │
│  Components: TextInput, Report, Highlights       │
└────────────────────┬────────────────────────────┘
                     │  REST API (Vite proxy)
┌────────────────────▼────────────────────────────┐
│               FastAPI Backend                    │
│  /api/v1/detect   → PlagiarismDetector           │
│  /api/v1/humanize → Humanizer (LLM / fallback)  │
│  /api/v1/pipeline → Detect+Humanize+Re-detect   │
│  /api/v1/reports  → SQLite persistence           │
├──────────────────────────────────────────────────┤
│  Services:                                       │
│  • sentence-transformers (all-MiniLM-L6-v2)     │
│  • AI detector (perplexity + burstiness)         │
│  • Rule-based fallback humanizer                 │
│  • HTML report generator                         │
└──────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Clone & Setup

```bash
git clone https://github.com/Ramdragneel01/plagguard.git
cd plagguard

# Backend
pip install -r requirements.txt

# Frontend
npm install
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — add your OpenAI or Anthropic API key for LLM humanization
# (The app works without an API key using rule-based fallback)
```

### 3. Run

```bash
# Terminal 1 — Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
npm run dev
```

Open **http://localhost:5173** → paste text → scan.

### Docker

```bash
docker compose up --build
# → http://localhost:8000
```

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/health` | GET | Health check |
| `/api/v1/detect` | POST | Plagiarism + AI detection |
| `/api/v1/humanize` | POST | Humanize text |
| `/api/v1/pipeline` | POST | Detect → Humanize → Re-detect |
| `/api/v1/reports` | GET | List saved reports |
| `/api/v1/reports/{id}` | GET | Get report JSON |
| `/api/v1/reports/{id}/html` | GET | Get report as HTML |
| `/docs` | GET | Swagger UI |

### Example — Detect

```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here with at least twenty characters.", "check_web": false}'
```

## 🔧 Tech Stack

- **Backend**: FastAPI, sentence-transformers, numpy, Pydantic v2
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite, Lucide icons
- **AI Detection**: Statistical analysis (perplexity, burstiness, vocabulary entropy)
- **Humanization**: OpenAI / Anthropic API + rule-based fallback
- **Database**: SQLite (WAL mode) — easily swappable to PostgreSQL
- **Containerization**: Docker multi-stage build

## 📊 How Detection Works

### Plagiarism Detection
1. **Sentence splitting** — text is broken into individual sentences
2. **Semantic embeddings** — each sentence is encoded via `all-MiniLM-L6-v2`
3. **Self-similarity** — finds recycled/repeated sentences within the document
4. **Corpus matching** — compares against a reference corpus (extensible)
5. **Web search** — optional Google Custom Search cross-reference
6. **Scoring** — weighted similarity produces an overall risk level

### AI Detection
1. **Perplexity** — bigram entropy measures predictability
2. **Burstiness** — sentence length variance (AI text is uniform)
3. **Vocabulary diversity** — hapax legomena ratio
4. **Sentence start diversity** — detects repetitive AI patterns
5. **Connector density** — AI overuses transition words

### Humanization
- **LLM mode**: Sends text to OpenAI/Anthropic with level-specific prompts
- **Fallback mode**: Rule-based — replaces formal connectors, adds contractions
- **Three levels**: Light (10% change), Moderate (40%), Heavy (70%)

## 📄 License

MIT

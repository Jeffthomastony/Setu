# Setu

AI-Powered Government Scheme & Opportunity Discovery Platform

*"Setu" means "bridge" — an intelligent bridge between citizens and public opportunities, reducing the information gap so people don't miss scholarships, schemes, and other opportunities they're eligible for.*

Team Flux — AI for Smarter Communities Hackathon

## What it does

The hackathon prototype focuses on students and government scholarships/schemes; the platform is designed to extend to internships, fellowships, skill development programs, and welfare initiatives, and to citizens beyond students (farmers, workers, senior citizens, persons with disabilities, job seekers) as future scope.

A student fills in a short profile (age, family income, category, state, education level, etc.), searches by keyword, or asks a question in plain language. Setu:

1. **Extracts** structured eligibility criteria from each scheme's raw eligibility text using an NLP pipeline (spaCy) — turning prose like *"No income limit for SC, ST and OEC students; annual family income below ₹1,00,000 for OBC students"* into clean, comparable rules.
2. **Ranks** every scheme against the student's profile using a semantic embedding model (spaCy word vectors) combined with hard eligibility checks, so close/overlooked matches surface too, not just exact keyword hits.
3. **Explains** every match with a criterion-by-criterion breakdown (✅/❌ per rule), plus the documents needed to apply.
4. **Answers questions** in plain language (e.g. "what documents do I need for NMMS?") by retrieving the most relevant scheme via the same embedding pipeline and filling a template from that scheme's structured data — grounded in the actual dataset rather than freely generated, so it can't invent facts about a scheme.

No student data is ever saved or sent anywhere — matching happens entirely in-memory for the duration of the request.

## Project structure

```
backend/            FastAPI app (the AI/matching engine)
  app/
    data/            schemes.json — the scheme knowledge base
    extraction/       NLP criteria extraction (spaCy)
    matching/         embeddings + matching/scoring engine
    qa/               retrieval + template-based question answering
    api/              FastAPI routes
    models.py         request/response schemas
    main.py           app entrypoint
  scripts/
    test_matching.py  quick manual sanity check, no server needed
  requirements.txt

frontend/            React app (Vite) — landing page, search, profile form, and Q&A UI
```

## Running it locally (for beginners)

You'll need **Python 3.10+**, **Node.js 18+**, and **npm** installed.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_md

uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`. Check `http://localhost:8000/health`.

To sanity-check the matching logic without starting a server:

```bash
python scripts/test_matching.py
```

### 2. Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. Fill in the form and click "Find my schemes".

## Adding more schemes

Add a new entry to `backend/app/data/schemes.json` following the same shape as the existing entries. No code changes needed — the extraction, matching, search, and Q&A pipelines all pick it up automatically.

## Why this counts as "AI, not just an API wrapper"

- **NLP extraction**: eligibility fields (income ceilings, academic percentage thresholds, class/education ranges) are still free text in the source data; `app/extraction/criteria_extractor.py` uses spaCy (sentence segmentation, tokenization, lemmatization) plus targeted parsing to turn that prose into structured, comparable values.
- **Recommendation system**: `app/matching/matcher.py` combines hard eligibility-criteria scoring with a semantic embedding similarity score (spaCy word vectors) to rank schemes by genuine relevance, not rigid keyword rules. The same embedding approach powers keyword `/search`.
- **Retrieval-grounded Q&A**: `app/qa/answer_engine.py` embeds a free-text question, retrieves the most relevant scheme via cosine similarity, classifies what's being asked (eligibility/income/documents/deadline/benefits/application process), and fills an answer template from that scheme's structured fields. It's deliberately *not* a free-generation chatbot — answers are traceable to specific dataset fields, so it can't hallucinate facts about a scheme, and it declines to answer when nothing matches confidently.
- **Explainable AI**: every match returns a full criterion-by-criterion breakdown of why it did or didn't qualify; every Q&A answer names which scheme and which fields it came from.
- **Privacy-first / responsible AI**: student profile data and questions are processed in-memory for the single request and never persisted, logged, or transmitted elsewhere.

## Future scope

- Live web search + extraction pipeline to automatically ingest new schemes from government portals, on top of the curated dataset.
- Optional account creation to save a profile for returning users (would need to be reconciled with the privacy-first design above).
- Expand the dataset beyond scholarships to internships, fellowships, skill development programs, and welfare initiatives, and beyond students to other citizen groups (farmers, workers, senior citizens, persons with disabilities, job seekers).

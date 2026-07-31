# Setu

AI-Powered Scheme & Scholarship Discovery

*"Setu" means "bridge" — a tool that bridges students and the support they qualify for but never hear about.*

Team Flux — AI for Smarter Communities Hackathon

## What it does

A student fills in a short profile (age, family income, category, state, education level, etc.). Setu:

1. **Extracts** structured eligibility criteria from each scheme's raw eligibility text using an NLP pipeline (spaCy) — turning prose like *"No income limit for SC, ST and OEC students; annual family income below ₹1,00,000 for OBC students"* into clean, comparable rules.
2. **Ranks** every scheme against the student's profile using a semantic embedding model (spaCy word vectors) combined with hard eligibility checks, so close/overlooked matches surface too, not just exact keyword hits.
3. **Explains** every match with a criterion-by-criterion breakdown (✅/❌ per rule), plus the documents needed to apply.

No student data is ever saved or sent anywhere — matching happens entirely in-memory for the duration of the request.

## Project structure

```
backend/            FastAPI app (the AI/matching engine)
  app/
    data/            schemes.json — the scheme knowledge base
    extraction/       NLP criteria extraction (spaCy)
    matching/         embeddings + matching/scoring engine
    api/              FastAPI routes
    models.py         request/response schemas
    main.py           app entrypoint
  scripts/
    test_matching.py  quick manual sanity check, no server needed
  requirements.txt

frontend/            React app (Vite) — student form + results UI
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

Add a new entry to `backend/app/data/schemes.json` following the same shape as the existing three (Kerala e-Grantz, NMMS, Snehapoorvam). No code changes needed — the extraction and matching pipeline picks it up automatically.

## Why this counts as "AI, not just an API wrapper"

- **NLP extraction**: eligibility fields (income ceilings, academic percentage thresholds, class/education ranges) are still free text in the source data; `app/extraction/criteria_extractor.py` uses spaCy (sentence segmentation, tokenization, lemmatization) plus targeted parsing to turn that prose into structured, comparable values.
- **Recommendation system**: `app/matching/matcher.py` combines hard eligibility-criteria scoring with a semantic embedding similarity score (spaCy word vectors) to rank schemes by genuine relevance, not rigid keyword rules.
- **Explainable AI**: every match returns a full criterion-by-criterion breakdown of why it did or didn't qualify.
- **Privacy-first / responsible AI**: student profile data is processed in-memory for the single request and never persisted, logged, or transmitted elsewhere.

## Future scope

- Live web search + extraction pipeline to automatically ingest new schemes from government portals, on top of the curated dataset.
- Optional account creation to save a profile for returning users (would need to be reconciled with the privacy-first design above).
- Expand the dataset beyond Kerala schemes to other states and central government schemes.

# Setu

AI-Powered Government Scheme & Opportunity Discovery Platform

*"Setu" means "bridge" — an intelligent bridge between citizens and public opportunities, reducing the information gap so people don't miss scholarships, schemes, and other opportunities they're eligible for.*

Team Flux — AI for Smarter Communities Hackathon

## What it does

The hackathon prototype focuses on students and government scholarships/schemes; the platform is designed to extend to other opportunity types and other citizen groups (farmers, workers, senior citizens, persons with disabilities, job seekers) as future scope.

A student either fills in a short profile, or searches by keyword. Setu:

1. **Extracts** structured eligibility criteria from each scheme's raw eligibility text using an NLP pipeline (spaCy) — turning prose like *"No income limit for SC, ST and OEC students; annual family income below ₹1,00,000 for OBC students"* into clean, comparable rules: income ceilings (general/by-category/rural-urban), academic percentage thresholds, class/education ranges, gender restrictions, age ranges, disability requirements, and orphan/single-parent targeting.
2. **Ranks** every scheme against the student's profile using a semantic embedding model (spaCy word vectors) combined with the extracted eligibility checks. The two are blended with an **adaptive weight**: schemes with richer extracted criteria lean more on the rule-based score (up to 65%), while schemes with sparse/ambiguous eligibility text lean more on semantic similarity (down to 40% criteria weight) — so the AI compensates when the structured extraction has less to go on.
3. **Explains** every match with a criterion-by-criterion breakdown (✅/❌ per rule), a plain-language AI-generated match summary ("Strong match — you qualify on 4 of 5 criteria..."), and the documents needed to apply.
4. **Searches** by keyword using a hybrid of literal keyword hits (name/department/description/eligibility text) and semantic embedding similarity, so both exact scheme names and loosely-worded queries surface relevant results.
5. **Generates a plain-language explanation** of any scheme on demand (`/explain/{scheme_id}`) — synthesizing the extracted structured criteria into a natural-language paragraph describing who the scheme targets, without re-reading the raw eligibility text.

The student's state input is also fuzzy-normalized against the canonical list of Indian states/UTs (e.g. "Kerla" → "Kerala") before matching, so small typos don't silently produce zero results.

No student data is ever saved or sent anywhere — matching happens entirely in-memory for the duration of the request.

## Project structure

```
backend/            FastAPI app (the AI/matching engine)
  app/
    data/            schemes.json — the scheme knowledge base (72 entries)
    extraction/       NLP criteria extraction (spaCy)
    matching/         embeddings + adaptive-weighted matching/scoring engine
    qa/               retrieval-grounded Q&A over a scheme's structured data
    api/              FastAPI routes (match, search, explain, ask, schemes, health)
    models.py         request/response schemas
    main.py           app entrypoint (pre-warms spaCy models on startup)
  scripts/
    test_matching.py  quick manual sanity check, no server needed
  requirements.txt

frontend/            React app (Vite)
  src/
    components/
      LandingPage.jsx    entry point: Search Schemes / Scholarships For You
      SearchPage.jsx      keyword + semantic search UI
      StudentForm.jsx     profile form (incl. optional religion, institution type)
      ResultCard.jsx       ranked result with match summary + on-demand AI explanation/Q&A
      LoadingScreen.jsx    animated splash shown while the app initializes
      Logo.jsx             reusable SVG bridge-motif logo
    App.jsx             view routing + client-side profile summary
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

**Windows + Python 3.13 note**: `requirements.txt` pins `spacy==3.7.5`, which doesn't have prebuilt wheels for Python 3.13 and will fail to compile from source. If `pip install -r requirements.txt` fails on spaCy/thinc/blis build errors, install spaCy unpinned instead: `pip install fastapi "uvicorn[standard]" pydantic numpy spacy`, then continue with the spaCy model downloads above.

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

Open `http://localhost:5173` in your browser (or the next port Vite picks if 5173 is busy — the backend's CORS config already allows 5173–5176).

## API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /schemes` | Lightweight listing of all schemes (debug/admin use) |
| `POST /match` | Full profile-based matching — returns ranked schemes scoring ≥70% |
| `GET /search?q=` | Keyword + semantic search — returns up to 10 results scoring ≥30% |
| `GET /explain/{scheme_id}` | AI-generated plain-language explanation of a scheme's eligibility |
| `GET /ask/{scheme_id}?q=` | Retrieval-grounded Q&A — answers a free-text question about one scheme, sourced from its structured data |

## Adding more schemes

Add a new entry to `backend/app/data/schemes.json` following the same shape as the existing 72. No code changes needed — extraction, matching, search, and explanation all pick it up automatically. The dataset currently spans 20 states plus national-level schemes, across scheme types including merit, post-matric, pre-matric, welfare, disability, girl-education, research fellowship, overseas scholarship, and coaching-support schemes.

## Why this counts as "AI, not just an API wrapper"

- **NLP extraction**: eligibility fields (income ceilings, percentage thresholds, class/education ranges, age ranges, gender/disability restrictions) are free text in the source data; `app/extraction/criteria_extractor.py` uses spaCy (sentence segmentation, tokenization, lemmatization) plus targeted parsing to turn that prose into structured, comparable values.
- **Adaptive recommendation system**: `app/matching/matcher.py` blends hard eligibility-criteria scoring with a semantic embedding similarity score, weighting each dynamically based on how much structured criteria could actually be extracted for a given scheme — not a fixed rule set.
- **Generative explanation**: `/explain/{scheme_id}` turns the extracted structured criteria back into a natural-language paragraph (NLG), grounded in the actual extracted data, not free-form generation from an external model. (The frontend's match/profile summary text is plain client-side templating over the real match results — not a model — and is labelled as such in the code.)
- **Retrieval-grounded Q&A**: `/ask/{scheme_id}` (`app/qa/qa_engine.py`) turns a scheme's structured fields into a set of fact sentences, ranks them against a free-text question with the same semantic + keyword blend as search, and returns the top-matching facts verbatim — so answers are always traceable to a real field in the scheme record, never freely generated.
- **Explainable AI**: every match returns a full criterion-by-criterion breakdown of why it did or didn't qualify.
- **Privacy-first / responsible AI**: student profile data is processed in-memory for the single request and never persisted, logged, or transmitted elsewhere.

## Future scope

- Live web search + extraction pipeline to automatically ingest new schemes from government portals, on top of the curated dataset.
- Optional account creation to save a profile for returning users (would need to be reconciled with the privacy-first design above).
- Expand beyond scholarships/schemes to internships and skill development programs, and beyond students to other citizen groups (farmers, workers, senior citizens, persons with disabilities, job seekers).

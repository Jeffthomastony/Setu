# Setu

AI-Powered Government Scheme & Opportunity Discovery Platform

*"Setu" means "bridge" — an intelligent bridge between citizens and public opportunities, reducing the information gap so people don't miss scholarships, schemes, and other opportunities they're eligible for.*

Team Flux — AI for Smarter Communities Hackathon

## What it does

The hackathon prototype covers two citizen groups today — **students** and **senior citizens** — matched against government scholarships/schemes/pensions; the platform is designed to extend to further opportunity types and citizen groups (farmers, workers, persons with disabilities, job seekers) as future scope.

A student or senior citizen either fills in a short profile, or searches by keyword. Setu:

1. **Extracts** structured eligibility criteria from each scheme's raw eligibility text using an NLP pipeline (spaCy) — turning prose like *"No income limit for SC, ST and OEC students; annual family income below ₹1,00,000 for OBC students"* into clean, comparable rules: income ceilings (general/by-category/rural-urban), academic percentage thresholds, class/education ranges, gender restrictions, age ranges, disability requirements, and orphan/single-parent targeting.
2. **Ranks** every scheme against the student's profile using a sentence-transformer embedding model (`all-MiniLM-L6-v2`) combined with the extracted eligibility checks. The two are blended with an **adaptive weight**: schemes with richer extracted criteria lean more on the rule-based score (up to 65%), while schemes with sparse/ambiguous eligibility text lean more on semantic similarity (down to 40% criteria weight) — so the AI compensates when the structured extraction has less to go on.
3. **Explains** every match with a criterion-by-criterion breakdown (✅/❌ per rule), a plain-language AI-generated match summary ("Strong match — you qualify on 4 of 5 criteria..."), and the documents needed to apply.
4. **Searches** by keyword using a hybrid of literal keyword hits (name/department/description/eligibility text) and sentence-transformer semantic similarity, so both exact scheme names and loosely-worded queries surface relevant results.
5. **Generates a plain-language explanation** of any scheme on demand (`/explain/{scheme_id}`) — synthesizing the extracted structured criteria into a natural-language paragraph describing who the scheme targets, without re-reading the raw eligibility text.

The applicant's state input is also fuzzy-normalized against the canonical list of Indian states/UTs (e.g. "Kerla" → "Kerala") before matching, so small typos don't silently produce zero results.

No applicant data is ever saved or sent anywhere — matching happens entirely in-memory for the duration of the request.

**Senior citizens** get the same matching pipeline through a separate profile (`SeniorCitizenProfile`: age, income, category, state, gender, disability, plus optional marital status, ration-card type, and living arrangement) and a dedicated dataset of 16 real, verified pension/health/assistive-device schemes (`POST /match/senior`) — reusing the same NLP extraction, adaptive-weighted scoring, explain, and Q&A engines. Marital status and ration-card type aren't just semantic hints — schemes that gate on widowhood (e.g. the Widow Pension Scheme) or BPL status are checked as explicit, explainable rule-based criteria, the same way income and age are.

## Project structure

```
backend/            FastAPI app (the AI/matching engine)
  app/
    data/            schemes.json — student/general scheme knowledge base (57 entries)
                     senior_citizen_schemes.json — senior-citizen scheme knowledge base (16 entries)
                     both verified real with working official links
    extraction/       NLP criteria extraction (spaCy)
    matching/         embeddings + adaptive-weighted matching/scoring engine
                     (match_student + match_senior_citizen, sharing the same criterion checkers)
                     cache.py — pre-computed/cached scheme criteria + embeddings so a
                     /match request only pays the cost of embedding the applicant's own text
    qa/               retrieval-grounded Q&A over a scheme's structured data
    api/              FastAPI routes (match, match/senior, search, explain, ask, schemes, health)
                     city→state resolution (e.g. "Mumbai" → "Maharashtra") on top of typo correction
    models.py         request/response schemas
    main.py           app entrypoint (pre-warms spaCy + embedding models, warms the scheme cache)
  scripts/
    test_matching.py     quick manual sanity check, no server needed
    validate_schemes.py  data-quality gate — runs the real extractor against every scheme and
                         flags unparsed age/income fields, duplicate IDs, and placeholder links
  requirements.txt

frontend/            React app (Vite)
  src/
    components/
      LandingPage.jsx      entry point: Search Schemes / Scholarships For You / Schemes For Senior Citizens
                           (scheme/state counts are fetched live, not hardcoded)
      SearchPage.jsx        keyword + semantic search UI
      StudentForm.jsx       student profile form (incl. optional religion, institution type)
      SeniorCitizenForm.jsx senior citizen profile form (age, income, category, state, gender,
                           disability, marital status, ration-card type, living arrangement)
      ResultCard.jsx         ranked result with match summary, on-demand AI explanation/Q&A,
                           benefit highlights, and a text-to-speech "Listen" button
      LoadingScreen.jsx      animated splash shown while the app initializes
      Logo.jsx               reusable SVG bridge-motif logo
    App.jsx             view routing, shared MatchFlow (form+results, results filter bar,
                        persisted form data on Back) for both citizen groups, client-side
                        profile summaries, "Senior-Friendly View" high-contrast/large-text toggle
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

uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`. Check `http://localhost:8000/health`.

**First run needs internet once**: the semantic-matching engine uses a sentence-transformer model (`all-MiniLM-L6-v2`, ~90MB) that downloads automatically from the Hugging Face Hub the first time the server starts, then caches locally under `~/.cache/huggingface` — no further internet needed after that. If the download can't complete (offline, blocked network), the app still runs; semantic scoring just falls back to neutral so rule-based eligibility matching keeps working.

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
| `GET /schemes` | Lightweight listing of all schemes across every dataset (debug/admin use) |
| `POST /match` | Student profile-based matching — returns ranked schemes scoring ≥55% |
| `POST /match/senior` | Senior citizen profile-based matching — returns ranked schemes scoring ≥55% |
| `GET /search?q=` | Keyword + semantic search across all datasets — returns up to 10 results scoring ≥30% |
| `GET /explain/{scheme_id}` | AI-generated plain-language explanation of a scheme's eligibility (any dataset) |
| `GET /ask/{scheme_id}?q=` | Retrieval-grounded Q&A — answers a free-text question about one scheme, sourced from its structured data (any dataset) |

## Adding more schemes

Add a new entry to `backend/app/data/schemes.json` (students/general) or `backend/app/data/senior_citizen_schemes.json` (senior citizens) following the same shape as the existing entries. No code changes needed — extraction, matching, search, explain, and ask all pick it up automatically since `/explain` and `/ask` look up scheme IDs across every dataset. The student dataset spans 19 states plus national-level schemes, across scheme types including merit, post-matric, pre-matric, welfare, disability, girl-education, research fellowship, overseas scholarship, and coaching-support schemes; the senior-citizen dataset spans old-age pension, widow/disability pension, assistive-device, and health-insurance schemes across 11 states plus national coverage. Every entry in both datasets has been checked against an official/verified source and a working application or information link — no placeholder or mock data.

**Before committing new/edited scheme entries**, run `python scripts/validate_schemes.py` — it runs the real extraction pipeline against every scheme and fails if an age/income field doesn't actually parse into a structured value, or if a scheme_id/name is duplicated. This exists because that exact class of bug shipped once (several schemes phrased age as "60 years and above", which an earlier version of the extractor's regex didn't recognise, silently dropping the age check).

## Why this counts as "AI, not just an API wrapper"

- **NLP extraction**: eligibility fields (income ceilings, percentage thresholds, class/education ranges, age ranges, gender/disability restrictions) are free text in the source data; `app/extraction/criteria_extractor.py` uses spaCy (sentence segmentation, tokenization, lemmatization) plus targeted parsing to turn that prose into structured, comparable values.
- **Adaptive recommendation system**: `app/matching/matcher.py` blends hard eligibility-criteria scoring with a sentence-transformer semantic similarity score (`app/matching/embedder.py`, `all-MiniLM-L6-v2` via Hugging Face), weighting each dynamically based on how much structured criteria could actually be extracted for a given scheme — not a fixed rule set. The same extraction, embedding, and adaptive-weighting engine powers both `match_student` and `match_senior_citizen`, which share their demographic criterion-checkers (state/category/income/gender/age/disability) and differ only in which checks apply to each citizen group.
- **Generative explanation**: `/explain/{scheme_id}` turns the extracted structured criteria back into a natural-language paragraph (NLG), grounded in the actual extracted data, not free-form generation from an external model. (The frontend's match/profile summary text is plain client-side templating over the real match results — not a model — and is labelled as such in the code.)
- **Retrieval-grounded Q&A**: `/ask/{scheme_id}` (`app/qa/qa_engine.py`) turns a scheme's structured fields into a set of fact sentences, ranks them against a free-text question with the same semantic + keyword blend as search, and returns the top-matching facts verbatim — so answers are always traceable to a real field in the scheme record, never freely generated.
- **Explainable AI**: every match returns a full criterion-by-criterion breakdown of why it did or didn't qualify.
- **Privacy-first / responsible AI**: applicant profile data is processed in-memory for the single request and never persisted, logged, or transmitted elsewhere.

## Future scope

- Live web search + extraction pipeline to automatically ingest new schemes from government portals, on top of the curated dataset.
- Optional account creation to save a profile for returning users (would need to be reconciled with the privacy-first design above).
- Expand beyond scholarships/schemes to internships and skill development programs, and beyond students/senior citizens to further citizen groups (farmers, workers, persons with disabilities, job seekers).

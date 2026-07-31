import { useState } from "react";
import { askScheme, explainScheme } from "../api";

// ── Match summary — client-side template over the backend's real criteria breakdown ──
function generateMatchSummary(criteria_breakdown) {
  if (!criteria_breakdown || criteria_breakdown.length === 0) return null;

  const matched = criteria_breakdown.filter((c) => c.matched);
  const unmatched = criteria_breakdown.filter((c) => !c.matched);
  const total = criteria_breakdown.length;
  const matchedCount = matched.length;

  const listNames = (items) => {
    const names = items.map((c) => c.criterion.toLowerCase());
    if (names.length === 1) return names[0];
    return names.slice(0, -1).join(", ") + " and " + names.slice(-1)[0];
  };

  if (matchedCount === total) {
    return `✨ You meet all ${total} eligibility criteria for this scheme.`;
  }
  if (matchedCount === 0) {
    return `⚠️ None of the ${total} criteria are currently met — this is a low-confidence match based on semantic similarity only.`;
  }
  if (matchedCount >= Math.ceil(total * 0.75)) {
    const unmatchedStr = listNames(unmatched);
    const plural = unmatched.length === 1 ? "criterion is" : "criteria are";
    return `🟢 Strong match — you qualify on ${matchedCount} of ${total} criteria. Only ${unmatchedStr} ${plural} unmet.`;
  }
  if (matchedCount >= Math.ceil(total / 2)) {
    const matchedStr = listNames(matched.slice(0, 2));
    return `🟡 Partial match — ${matchedStr} align with your profile, but ${unmatched.length} ${unmatched.length === 1 ? "criterion" : "criteria"} ${unmatched.length === 1 ? "is" : "are"} unmet.`;
  }
  return `🔴 Low match — only ${matchedCount} of ${total} criteria are met. This scheme has specific requirements that may not fit your current profile.`;
}

// ── Confidence label from score ───────────────────────────────────────────────
function getConfidenceLabel(score) {
  if (score >= 90) return { label: "Excellent Match", tier: "excellent" };
  if (score >= 75) return { label: "Strong Match", tier: "strong" };
  if (score >= 60) return { label: "Good Match", tier: "good" };
  return { label: "Possible Match", tier: "possible" };
}

function ScoreBadge({ score, label, showConfidence = false }) {
  const cls =
    score >= 80 ? "score-high" : score >= 60 ? "score-mid" : "score-low";
  const confidence = showConfidence ? getConfidenceLabel(score) : null;

  return (
    <div className="score-badge-wrap">
      <span className={`score-badge ${cls}`} aria-label={`${score}% ${label}`}>
        {score}% {label}
      </span>
      {confidence && (
        <span className={`confidence-label confidence-${confidence.tier}`}>
          {confidence.label}
        </span>
      )}
    </div>
  );
}

function CriteriaItem({ criterion, matched, reason }) {
  return (
    <li className={`criteria-item ${matched ? "matched" : "unmatched"}`}>
      <span
        className={`criteria-status ${matched ? "matched" : "unmatched"}`}
        aria-label={matched ? "Met" : "Not met"}
      >
        {matched ? "✓" : "✕"}
      </span>
      <span className="criteria-text">
        <strong>{criterion}:</strong> {reason}
      </span>
    </li>
  );
}

// ── AI "Why this matched" panel ───────────────────────────────────────────────
function WhyMatchedPanel({ schemeId }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function handleToggle() {
    if (open) { setOpen(false); return; }
    setOpen(true);
    if (data || loading) return;
    setLoading(true);
    try {
      const result = await explainScheme(schemeId);
      setData(result);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="why-matched-wrap">
      <button
        className={`why-matched-btn ${open ? "open" : ""}`}
        onClick={handleToggle}
        type="button"
        aria-expanded={open}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
        {open ? "Hide" : "Why this matched"}
        <svg
          className={`why-chevron ${open ? "rotated" : ""}`}
          width="13" height="13" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="why-matched-panel animate-fade-up">
          {loading && (
            <div className="why-matched-loading">
              <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
              AI is analysing this scheme…
            </div>
          )}
          {error && (
            <p className="why-matched-error">
              Could not load explanation. Make sure the backend is running.
            </p>
          )}
          {data && !loading && (
            <>
              <p className="why-matched-text">{data.ai_explanation}</p>
              <div className="why-matched-meta">
                <span className="why-matched-richness">
                  📊 Criteria richness: {data.criteria_richness}/10
                </span>
                <span className="why-matched-note">
                  Higher richness = more rule-based matching, less guesswork
                </span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── AI "Ask about this scheme" panel (retrieval-grounded Q&A) ────────────────
function AskPanel({ schemeId }) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAsk(e) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await askScheme(schemeId, trimmed);
      setAnswer(result);
    } catch (err) {
      setError(err.message || "Could not get an answer.");
      setAnswer(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ask-panel-wrap">
      <button
        className={`why-matched-btn ${open ? "open" : ""}`}
        onClick={() => setOpen((o) => !o)}
        type="button"
        aria-expanded={open}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 2-3 4" />
          <path d="M12 17h.01" />
        </svg>
        {open ? "Hide" : "Ask about this scheme"}
        <svg
          className={`why-chevron ${open ? "rotated" : ""}`}
          width="13" height="13" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="why-matched-panel animate-fade-up">
          <p className="ask-hint" style={{ marginBottom: "10px" }}>
            Ask a question and get an answer sourced from this scheme's own eligibility,
            benefits, and application details — nothing is made up.
          </p>
          <form className="ask-form" onSubmit={handleAsk}>
            <input
              type="text"
              className="ask-input"
              placeholder="e.g. Is there an income limit? What documents do I need?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button type="submit" className="ask-submit-btn" disabled={loading || !question.trim()}>
              {loading ? "Asking…" : "Ask"}
            </button>
          </form>

          {loading && (
            <div className="why-matched-loading">
              <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
              Searching this scheme's data…
            </div>
          )}
          {error && <p className="why-matched-error">{error}</p>}
          {answer && !loading && (
            <div className="answer-card">
              <p className="answer-text">{answer.answer}</p>
              <p className="ask-disclaimer">
                Answer generated from {answer.scheme_name}'s official structured data —
                always confirm on the official website before applying.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ResultCard({ result, index = 0 }) {
  const delayClass = `delay-${Math.min(index * 100, 500)}`;

  // Detect shape: SchemeSearchResult has relevance_score; MatchResult has overall_score
  const isSearchResult = result.relevance_score !== undefined;
  const displayScore = isSearchResult ? result.relevance_score : result.overall_score;
  const scoreLabel = isSearchResult ? "relevance" : "match";

  return (
    <article
      className={`result-card animate-fade-up ${delayClass}`}
      aria-label={`Scheme: ${result.scheme_name}`}
    >
      {/* Header */}
      <div className="result-card-header">
        <h3 className="result-card-title">{result.scheme_name}</h3>
        <ScoreBadge
          score={displayScore}
          label={scoreLabel}
          showConfidence={!isSearchResult}
        />
      </div>

      {/* Department */}
      {result.department && (
        <p className="result-department">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            aria-hidden="true" style={{ flexShrink: 0 }}>
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
          {result.department}
        </p>
      )}

      {/* State tag — only for search results */}
      {isSearchResult && result.state && (
        <p className="result-department" style={{ marginTop: "4px" }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            aria-hidden="true" style={{ flexShrink: 0 }}>
            <path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          {result.state || "National"}
        </p>
      )}

      {/* Description — only for search results */}
      {isSearchResult && result.description && (
        <p style={{
          fontSize: "0.85rem",
          color: "var(--text-secondary, #888)",
          margin: "8px 0 0",
          lineHeight: 1.5,
        }}>
          {result.description}
        </p>
      )}

      {/* Match summary — only for match results */}
      {!isSearchResult && result.criteria_breakdown && (() => {
        const summary = generateMatchSummary(result.criteria_breakdown);
        return summary ? (
          <p style={{
            fontSize: "0.82rem",
            fontStyle: "italic",
            color: "var(--text-secondary, #aaa)",
            margin: "10px 0 4px",
            lineHeight: 1.5,
            borderLeft: "3px solid var(--accent, #6c63ff)",
            paddingLeft: "10px",
          }}>
            {summary}
          </p>
        ) : null;
      })()}

      {/* Score breakdown pills — only for match results */}
      {!isSearchResult && (
        <div className="score-breakdown">
          <span className="score-pill">
            <span className="score-pill-label">Eligibility:</span>
            {result.criteria_score}%
          </span>
          <span className="score-pill">
            <span className="score-pill-label">Relevance:</span>
            {result.semantic_score}%
          </span>
        </div>
      )}

      {/* Criteria breakdown — only for match results */}
      {!isSearchResult && result.criteria_breakdown && (
        <ul className="criteria-list">
          {result.criteria_breakdown.map((c) => (
            <CriteriaItem
              key={c.criterion}
              criterion={c.criterion}
              matched={c.matched}
              reason={c.reason}
            />
          ))}
        </ul>
      )}

      {/* AI "Why this matched" — only for match results */}
      {!isSearchResult && (
        <WhyMatchedPanel schemeId={result.scheme_id} />
      )}

      {/* AI "Ask about this scheme" — retrieval-grounded Q&A, all result types */}
      <AskPanel schemeId={result.scheme_id} />

      {/* Documents */}
      {result.required_documents?.length > 0 && (
        <details className="docs-details">
          <summary className="docs-summary">
            <span className="docs-summary-chevron">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </span>
            Documents you'll need ({result.required_documents.length})
          </summary>
          <ul className="docs-list">
            {result.required_documents.map((doc) => (
              <li key={doc}>{doc}</li>
            ))}
          </ul>
        </details>
      )}

      {/* Action links */}
      {(result.official_website || result.application_portal) && (
        <div className="result-links">
          {result.application_portal && (
            <a
              href={result.application_portal}
              target="_blank"
              rel="noreferrer"
              className="result-link-btn primary"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
              Apply Now
            </a>
          )}
          {result.official_website &&
            result.official_website !== result.application_portal && (
              <a
                href={result.official_website}
                target="_blank"
                rel="noreferrer"
                className="result-link-btn secondary"
              >
                Official Website
              </a>
            )}
        </div>
      )}
    </article>
  );
}

export default function ResultCard({ result }) {
  return (
    <article className="result-card">
      <header>
        <h3>{result.scheme_name}</h3>
        <span className="score-badge">{result.overall_score}% match</span>
      </header>

      {result.department && <p className="department">{result.department}</p>}

      <div className="score-breakdown-summary">
        <span>Eligibility fit: {result.criteria_score}%</span>
        <span>Relevance: {result.semantic_score}%</span>
      </div>

      <ul className="criteria-list">
        {result.criteria_breakdown.map((c) => (
          <li key={c.criterion} className={c.matched ? "matched" : "unmatched"}>
            <span className="mark">{c.matched ? "✅" : "❌"}</span>
            <span>
              <strong>{c.criterion}:</strong> {c.reason}
            </span>
          </li>
        ))}
      </ul>

      {result.required_documents?.length > 0 && (
        <details>
          <summary>Documents you'll need</summary>
          <ul>
            {result.required_documents.map((doc) => (
              <li key={doc}>{doc}</li>
            ))}
          </ul>
        </details>
      )}

      <div className="result-links">
        {result.official_website && (
          <a href={result.official_website} target="_blank" rel="noreferrer">
            Official website
          </a>
        )}
        {result.application_portal && result.application_portal !== result.official_website && (
          <a href={result.application_portal} target="_blank" rel="noreferrer">
            Apply here
          </a>
        )}
      </div>
    </article>
  );
}

import { useState } from "react";
import { askQuestion } from "../api";

export default function AskPage({ onBack }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAsk(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const data = await askQuestion(question.trim());
      setAnswer(data);
    } catch (err) {
      setError(err.message || "Couldn't get an answer. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="search-page">
      <button className="back-link" onClick={onBack}>
        &larr; Back
      </button>

      <h2>Ask a question</h2>
      <p className="ask-hint">
        Ask about a specific scheme's eligibility, documents, deadline, benefits, or how to apply.
      </p>

      <form className="search-form" onSubmit={handleAsk}>
        <input
          type="text"
          placeholder="e.g. What documents do I need for NMMS?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {error && <p className="error-banner">{error}</p>}

      {answer && (
        <article className="result-card answer-card">
          <p className="answer-text">{answer.answer}</p>

          {answer.scheme_name && (
            <>
              <div className="score-breakdown-summary">
                <span>Matched scheme: {answer.scheme_name}</span>
                <span>Confidence: {answer.confidence}%</span>
              </div>

              <div className="result-links">
                {answer.official_website && (
                  <a href={answer.official_website} target="_blank" rel="noreferrer">
                    Official website
                  </a>
                )}
                {answer.application_portal && answer.application_portal !== answer.official_website && (
                  <a href={answer.application_portal} target="_blank" rel="noreferrer">
                    Apply here
                  </a>
                )}
              </div>
            </>
          )}

          <p className="ask-disclaimer">
            This answer is generated from our scheme database, not live official sources — always confirm on the
            official website before applying.
          </p>
        </article>
      )}
    </div>
  );
}

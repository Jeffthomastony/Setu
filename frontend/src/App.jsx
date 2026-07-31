import { useState, useEffect } from "react";
import StudentForm from "./components/StudentForm";
import ResultCard from "./components/ResultCard";
import LandingPage from "./components/LandingPage";
import SearchPage from "./components/SearchPage";
import Logo from "./components/Logo";
import LoadingScreen from "./components/LoadingScreen";
import { matchStudent } from "./api";
import "./App.css";

// ── Profile summary generator (client-side template, not a model) ───────────
function generateProfileSummary(profile) {
  const income = profile.family_income;
  const incomeStr =
    income >= 100000
      ? `₹${(income / 100000).toFixed(1)} lakh`
      : `₹${income.toLocaleString("en-IN")}`;

  const cat = profile.category;
  const genderLabel =
    profile.gender === "female"
      ? "female"
      : profile.gender === "male"
      ? "male"
      : "non-binary";

  const line1 = `You're a ${profile.age}-year-old ${genderLabel} student from ${profile.state} (${profile.residence_area} area), category ${cat}, currently at ${profile.education_level} level — with an annual family income of ${incomeStr}.`;

  const perks = [];
  if (["SC", "ST"].includes(cat))
    perks.push("reserved-category benefits (SC/ST)");
  if (["OBC", "OEC"].includes(cat)) perks.push("OBC/OEC targeted schemes");
  if (profile.gender === "female") perks.push("girl-only scholarships");
  if (profile.disability) perks.push("disability-targeted welfare schemes");
  if (profile.parent_status !== "both_parents")
    perks.push("orphan/single-parent assistance schemes");
  if (income < 100000) perks.push("very low-income support programmes");
  else if (income < 250000) perks.push("low-income scholarship schemes");
  if (profile.residence_area === "rural") perks.push("rural development grants");
  if (profile.religion && !["prefer_not_to_say", "other", null].includes(profile.religion))
    perks.push(`minority community (${profile.religion}) scholarships`);

  const line2 =
    perks.length > 0
      ? `Your profile qualifies you for ${perks.slice(0, 3).join(", ")} — AI has scanned all schemes to surface your best matches.`
      : "AI has scanned all available schemes and ranked them for your profile.";

  return { line1, line2 };
}

function App() {
  const [view, setView] = useState("landing"); // 'landing' | 'search' | 'form'
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [submittedProfile, setSubmittedProfile] = useState(null);
  // Initial app splash screen
  const [appReady, setAppReady] = useState(false);
  const [initProgress, setInitProgress] = useState(0);
  const [initMessage, setInitMessage] = useState("Loading Setu");

  // Simulate a short initialisation sequence
  useEffect(() => {
    const steps = [
      { delay: 0,    progress: 20,  message: "Loading Setu" },
      { delay: 350,  progress: 55,  message: "Preparing AI models" },
      { delay: 750,  progress: 85,  message: "Fetching schemes" },
      { delay: 1100, progress: 100, message: "Ready" },
      { delay: 1400, progress: 100, message: "Ready", done: true },
    ];

    const timers = steps.map(({ delay, progress, message, done }) =>
      setTimeout(() => {
        setInitProgress(progress);
        setInitMessage(message);
        if (done) setAppReady(true);
      }, delay)
    );

    return () => timers.forEach(clearTimeout);
  }, []);

  // Scroll to top on view change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [view]);

  async function handleSubmit(profile) {
    setLoading(true);
    setError(null);
    setResults(null);
    setSubmittedProfile(profile);
    try {
      const data = await matchStudent(profile);
      setResults(data);
      setTimeout(() => {
        document.getElementById("results-section")?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 100);
    } catch (err) {
      setError(
        err.message ||
          "Something went wrong while matching. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  }

  function goHome() {
    setView("landing");
    setResults(null);
    setError(null);
    setSubmittedProfile(null);
  }

  // Show loading screen until app is ready
  if (!appReady) {
    return <LoadingScreen message={initMessage} progress={initProgress} />;
  }

  // Derive a plain-language summary of the submitted profile
  const profileSummary =
    submittedProfile && results ? generateProfileSummary(submittedProfile) : null;

  return (
    <div className="app-shell">
      {/* Sticky header — only when not on landing */}
      {view !== "landing" && (
        <header className="app-header-bar">
          <button
            className="logo-button"
            onClick={goHome}
            aria-label="Back to Setu home"
          >
            <Logo size={34} />
          </button>
        </header>
      )}

      {view === "landing" && <LandingPage onSelect={setView} />}

      {view === "search" && <SearchPage onBack={goHome} />}

      {view === "form" && (
        <main className="page-content">
          <button className="back-link" onClick={goHome} aria-label="Back to home">
            ← Back
          </button>

          <div className="form-header form-page">
            <h2>Scholarships For You</h2>
            <p className="form-subheading">
              Fill in your profile and get personalized, AI-ranked scholarships and government schemes.
            </p>
          </div>

          <StudentForm onSubmit={handleSubmit} loading={loading} />

          {error && (
            <p className="error-banner" role="alert">
              ⚠️ {error}
            </p>
          )}

          {/* ── Minimal loading indicator ── */}
          {loading && (
            <>
              {/* Thin animated gradient rail pinned to top of viewport */}
              <div style={{
                position: "fixed",
                top: 0, left: 0, right: 0,
                height: "2px",
                zIndex: 300,
                background: "var(--clr-surface-2)",
                overflow: "hidden",
              }}>
                <div className="loading-progress-indeterminate" />
              </div>

              {/* Small inline status row below the form */}
              <div className="match-loading-row" role="status" aria-live="polite">
                <span className="setu-spinner" style={{ width: 13, height: 13, borderWidth: 1.5 }} />
                <span className="match-loading-label">
                  <span className="match-loading-ai">AI</span>
                  scanning schemes for your profile…
                </span>
              </div>
            </>
          )}


          {results && (
            <section
              id="results-section"
              className="results-section"
              aria-live="polite"
            >
              {/* Profile Summary Panel */}
              {profileSummary && (
                <div className="ai-insight-panel animate-fade-up">
                  <div className="ai-insight-header">
                    <span className="ai-insight-icon">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                      </svg>
                    </span>
                    <span className="ai-insight-title">Your Profile Summary</span>
                  </div>
                  <p className="ai-insight-line1">{profileSummary.line1}</p>
                  <p className="ai-insight-line2">{profileSummary.line2}</p>
                </div>
              )}

              <div className="results-header">
                <span className="results-title">Scholarships ranked for you</span>
                <span className="results-count-badge">{results.length}</span>
              </div>

              {results.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-state-icon">🎯</span>
                  <h3>No high-confidence matches found</h3>
                  <p>
                    No schemes passed the confidence threshold for your profile.
                    Try adjusting your details or check the Search tab for broader results.
                  </p>
                </div>
              ) : (
                <div className="results-list">
                  {results.map((r, i) => (
                    <ResultCard key={r.scheme_id} result={r} index={i} />
                  ))}
                </div>
              )}
            </section>
          )}
        </main>
      )}
    </div>
  );
}

export default App;

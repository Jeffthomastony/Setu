import Logo from "./Logo";

function TrustChip({ icon, label }) {
  return (
    <span className="trust-chip">
      <span>{icon}</span>
      {label}
    </span>
  );
}

function OptionCard({ icon, title, desc, onClick, delay }) {
  return (
    <button
      className={`landing-option animate-fade-up delay-${delay}`}
      onClick={onClick}
    >
      <div className="landing-option-icon" aria-hidden="true">
        {icon}
      </div>
      <div className="landing-option-body">
        <span className="landing-option-title">{title}</span>
        <span className="landing-option-desc">{desc}</span>
      </div>
      <span className="landing-option-arrow" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      </span>
    </button>
  );
}

const SearchIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" />
    <path d="m21 21-4.35-4.35" />
  </svg>
);

const FormIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 11l3 3L22 4" />
    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
  </svg>
);

const SeniorIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" />
    <path d="M9 21v-3M15 21v-3" />
  </svg>
);

export default function LandingPage({ onSelect }) {
  return (
    <div className="landing">
      {/* Hero */}
      <section className="landing-hero">
        <div className="hero-badge animate-fade-up">
          <span className="hero-badge-dot" />
          AI-Powered · Free · Private
        </div>

        <div className="landing-logo-hero">
          <Logo size={88} white />
        </div>

        <p className="landing-tagline">
          <em>"Setu"</em> means bridge — we connect students and senior citizens
          with scholarships and government schemes they qualify for but never
          hear about.
        </p>

        <div className="landing-stats animate-fade-up delay-200">
          <span className="landing-stat">
            <strong>72+</strong> verified schemes
          </span>
          <span className="landing-stat-divider">·</span>
          <span className="landing-stat">
            <strong>20+</strong> states covered
          </span>
          <span className="landing-stat-divider">·</span>
          <span className="landing-stat">
            <strong>100%</strong> free &amp; private
          </span>
        </div>

        <div className="landing-trust animate-fade-up delay-300">
          <TrustChip icon="🔒" label="Privacy-first" />
          <TrustChip icon="🧠" label="AI-matched" />
          <TrustChip icon="⚡" label="Instant results" />
          <TrustChip icon="📋" label="Explained matches" />
        </div>

        {/* Diagonal bottom cut */}
        <div className="landing-hero-bottom" aria-hidden="true" />
      </section>

      {/* Option cards */}
      <section className="landing-options-section">
        <span className="landing-options-label">How would you like to start?</span>

        <div className="landing-options">
          <OptionCard
            icon={<SearchIcon />}
            title="Search Schemes"
            desc="Look up a specific scheme or scholarship by name or keyword"
            onClick={() => onSelect("search")}
            delay="300"
          />
          <OptionCard
            icon={<FormIcon />}
            title="Scholarships For You"
            desc="Fill in your profile and get personalized, AI-ranked scholarships and government schemes"
            onClick={() => onSelect("form")}
            delay="400"
          />
          <OptionCard
            icon={<SeniorIcon />}
            title="Schemes For Senior Citizens"
            desc="Fill in a senior citizen's profile and get personalized pension, health, and welfare schemes"
            onClick={() => onSelect("senior-form")}
            delay="500"
          />
        </div>
      </section>
    </div>
  );
}

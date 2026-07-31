import Logo from "./Logo";

export default function LandingPage({ onSelect }) {
  return (
    <div className="landing">
      <Logo size={72} />
      <p className="tagline">
        "Setu" means bridge — find the scholarships and government schemes you qualify for but never hear about.
      </p>

      <div className="landing-options">
        <button className="landing-option" onClick={() => onSelect("search")}>
          <span className="landing-option-title">Search</span>
          <span className="landing-option-desc">Look up a specific scheme or scholarship by name or keyword</span>
        </button>

        <button className="landing-option" onClick={() => onSelect("form")}>
          <span className="landing-option-title">Fill in Details</span>
          <span className="landing-option-desc">Get personalized, ranked matches based on your profile</span>
        </button>
      </div>
    </div>
  );
}

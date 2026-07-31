import { useState, useMemo } from "react";

const INDIAN_STATES = [
  // States
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
  "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
  "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
  "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
  "West Bengal",
  // UTs
  "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli",
  "Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
  "Lakshadweep", "Puducherry",
];

const CATEGORIES = ["General", "OBC", "SC", "ST", "OEC"];

const MARITAL_STATUSES = [
  { value: "married", label: "Married" },
  { value: "widowed", label: "Widowed" },
  { value: "single", label: "Single / Unmarried" },
  { value: "divorced_abandoned", label: "Divorced / Abandoned / Destitute" },
];

const RATION_CARD_TYPES = [
  { value: "bpl", label: "BPL (Below Poverty Line) Card" },
  { value: "aay_antyodaya", label: "Antyodaya Anna Yojana (AAY / Poorest BPL)" },
  { value: "priority_household", label: "Priority Household (PHH) Card" },
  { value: "apl", label: "APL (Above Poverty Line) Card" },
  { value: "none", label: "No Ration Card / Unsure" },
];

const LIVING_STATUSES = [
  { value: "with_family", label: "Living with Family / Children" },
  { value: "living_alone", label: "Living Alone / No Dependents" },
  { value: "old_age_home", label: "Living in Old Age Home / Care Facility" },
];

const INITIAL_STATE = {
  age: "",
  family_income: "",
  category: "General",
  state: "Kerala",
  residence_area: "rural",
  gender: "female",
  disability: false,
  marital_status: "married",
  ration_card_type: "bpl",
  living_status: "with_family",
};

function FormField({ label, hint, error, children }) {
  return (
    <div className="form-field">
      <label>
        {label}
        {hint && <span className="field-hint">({hint})</span>}
      </label>
      {children}
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}

export default function SeniorCitizenForm({ onSubmit, loading, initialData, onDataChange }) {
  const [form, setForm] = useState(initialData || INITIAL_STATE);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [stateSearch, setStateSearch] = useState("");

  const filteredStates = useMemo(
    () =>
      INDIAN_STATES.filter((s) =>
        s.toLowerCase().includes(stateSearch.toLowerCase())
      ),
    [stateSearch]
  );

  function update(field, value) {
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      if (onDataChange) onDataChange(next);
      return next;
    });
    if (touched[field]) validate({ ...form, [field]: value });
  }

  function touch(field) {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }

  function validate(values = form) {
    const errs = {};
    if (!values.age || Number(values.age) < 60 || Number(values.age) > 120)
      errs.age = "Enter a valid age (60–120)";
    if (values.family_income === "" || Number(values.family_income) < 0)
      errs.family_income = "Enter a valid annual income (₹)";
    if (!values.state.trim()) errs.state = "State is required";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const allTouched = Object.keys(INITIAL_STATE).reduce(
      (a, k) => ({ ...a, [k]: true }),
      {}
    );
    setTouched(allTouched);
    if (!validate()) return;

    const payload = {
      age: Number(form.age),
      family_income: Number(form.family_income),
      category: form.category,
      state: form.state.trim(),
      residence_area: form.residence_area,
      gender: form.gender,
      disability: form.disability,
      marital_status: form.marital_status || null,
      ration_card_type: form.ration_card_type || null,
      living_status: form.living_status || null,
    };
    onSubmit(payload);
  }

  function inputClass(field) {
    if (!touched[field]) return "";
    return errors[field] ? "invalid" : "valid";
  }

  return (
    <form className="student-form" onSubmit={handleSubmit} noValidate>
      {/* Caregiver / Assistance Banner */}
      <div className="caregiver-banner">
        <span className="caregiver-icon">👵👴</span>
        <div className="caregiver-text">
          <strong>Filling on behalf of a parent or elderly relative?</strong>
          <span>You can assist them in answering these questions. All details remain private to this session.</span>
        </div>
      </div>

      <div className="privacy-note">
        <span className="privacy-note-icon">🔒</span>
        <span>
          Your details are used <strong>only for this session</strong> to
          compute matches — they are never saved, logged, or sent anywhere else.
        </span>
      </div>

      {/* SECTION 1: Personal */}
      <div className="form-section">
        <div className="form-section-title">
          <span className="form-section-num">1</span>
          Personal Details
        </div>

        <div className="form-grid">
          <FormField label="Age (Years)" hint="60 or above" error={touched.age && errors.age}>
            <input
              type="number"
              className={inputClass("age")}
              placeholder="e.g. 68"
              min="60"
              max="120"
              value={form.age}
              onChange={(e) => update("age", e.target.value)}
              onBlur={() => touch("age")}
            />
          </FormField>

          <FormField label="Gender">
            <select
              value={form.gender}
              onChange={(e) => update("gender", e.target.value)}
            >
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other / Prefer not to say</option>
            </select>
          </FormField>

          <FormField label="Category">
            <select
              value={form.category}
              onChange={(e) => update("category", e.target.value)}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </FormField>

          <FormField label="Marital Status" hint="Unlocks widow & destitution pensions">
            <select
              value={form.marital_status}
              onChange={(e) => update("marital_status", e.target.value)}
            >
              {MARITAL_STATUSES.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </FormField>
        </div>
      </div>

      {/* SECTION 2: Location */}
      <div className="form-section">
        <div className="form-section-title">
          <span className="form-section-num">2</span>
          Location
        </div>

        <div className="form-grid">
          <FormField label="State / Union Territory" error={touched.state && errors.state}>
            <select
              className={inputClass("state")}
              value={form.state}
              onChange={(e) => update("state", e.target.value)}
              onBlur={() => touch("state")}
            >
              {INDIAN_STATES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </FormField>

          <FormField label="Residence Area">
            <select
              value={form.residence_area}
              onChange={(e) => update("residence_area", e.target.value)}
            >
              <option value="rural">Rural (Panchayat / Village)</option>
              <option value="urban">Urban (Municipality / City)</option>
            </select>
          </FormField>
        </div>
      </div>

      {/* SECTION 3: Economic & Welfare */}
      <div className="form-section">
        <div className="form-section-title">
          <span className="form-section-num">3</span>
          Economic &amp; Welfare Details
        </div>

        <div className="form-grid">
          <FormField
            label="Annual Family Income (₹)"
            hint="Combined family/household income"
            error={touched.family_income && errors.family_income}
          >
            <input
              type="number"
              className={inputClass("family_income")}
              placeholder="e.g. 60000"
              min="0"
              value={form.family_income}
              onChange={(e) => update("family_income", e.target.value)}
              onBlur={() => touch("family_income")}
            />
          </FormField>

          <FormField label="Ration Card / Economic Card" hint="Unlocks BPL-restricted pensions">
            <select
              value={form.ration_card_type}
              onChange={(e) => update("ration_card_type", e.target.value)}
            >
              {RATION_CARD_TYPES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </FormField>

          <FormField label="Living Arrangement">
            <select
              value={form.living_status}
              onChange={(e) => update("living_status", e.target.value)}
            >
              {LIVING_STATUSES.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </FormField>

        </div>
      </div>

      {/* Disability — uses same styled checkbox-field as StudentForm */}
      <div
        className="checkbox-field"
        onClick={() => update("disability", !form.disability)}
        role="presentation"
        tabIndex={-1}
      >
        <input
          id="field-senior-disability"
          type="checkbox"
          checked={form.disability}
          onChange={(e) => update("disability", e.target.checked)}
          onClick={(e) => e.stopPropagation()}
        />
        <div>
          <div className="checkbox-field-label">I have a disability / physical impairment</div>
          <div className="checkbox-field-sub">
            Unlocks assistive-device grants (wheelchairs, hearing aids, spectacles) and disability pensions
          </div>
        </div>
      </div>


      <button
        type="submit"
        className="submit-btn"
        disabled={loading}
      >
        {loading ? (
          <>
            <span className="setu-spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
            Matching Senior Citizen Schemes…
          </>
        ) : (
          <>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
            Find My Schemes
          </>
        )}
      </button>
    </form>
  );
}

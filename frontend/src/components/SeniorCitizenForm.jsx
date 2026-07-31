import { useState } from "react";

const CATEGORIES = ["General", "OBC", "SC", "ST", "OEC"];

const INDIAN_STATES = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  // Union Territories
  "Andaman and Nicobar Islands",
  "Chandigarh",
  "Dadra and Nagar Haveli",
  "Daman and Diu",
  "Delhi",
  "Jammu and Kashmir",
  "Ladakh",
  "Lakshadweep",
  "Puducherry",
];

const CATEGORY_HINTS = {
  General: "No reservation category",
  OBC: "Other Backward Classes",
  SC: "Scheduled Castes",
  ST: "Scheduled Tribes",
  OEC: "Other Eligible Communities (Kerala)",
};

const INITIAL_STATE = {
  age: "",
  family_income: "",
  category: "General",
  state: "Kerala",
  residence_area: "rural",
  gender: "female",
  disability: false,
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

export default function SeniorCitizenForm({ onSubmit, loading }) {
  const [form, setForm] = useState(INITIAL_STATE);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
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
    };
    onSubmit(payload);
  }

  function inputClass(field) {
    if (!touched[field]) return "";
    return errors[field] ? "invalid" : "valid";
  }

  return (
    <form className="student-form" onSubmit={handleSubmit} noValidate>
      <div className="privacy-note">
        <span className="privacy-note-icon">🔒</span>
        <span>
          Your details are used <strong>only for this session</strong> to
          compute matches — they are never saved, logged, or sent anywhere else.
        </span>
      </div>

      {/* Personal Details */}
      <p className="form-section-title">Personal Details</p>
      <div className="form-grid">
        <FormField label="Age" error={touched.age && errors.age}>
          <input
            id="field-age"
            type="number"
            min="60"
            max="120"
            value={form.age}
            onChange={(e) => update("age", e.target.value)}
            onBlur={() => touch("age")}
            placeholder="e.g. 68"
            className={inputClass("age")}
          />
        </FormField>

        <FormField label="Gender">
          <select
            id="field-gender"
            value={form.gender}
            onChange={(e) => update("gender", e.target.value)}
          >
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other / Prefer not to say</option>
          </select>
        </FormField>

        <FormField label="Category" hint={CATEGORY_HINTS[form.category]}>
          <select
            id="field-category"
            value={form.category}
            onChange={(e) => update("category", e.target.value)}
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </FormField>
      </div>

      {/* Location */}
      <p className="form-section-title">Location</p>
      <div className="form-grid">
        <FormField label="State" error={touched.state && errors.state}>
          <select
            id="field-state"
            value={form.state}
            onChange={(e) => update("state", e.target.value)}
            onBlur={() => touch("state")}
            className={inputClass("state")}
          >
            {INDIAN_STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Residence area">
          <select
            id="field-residence"
            value={form.residence_area}
            onChange={(e) => update("residence_area", e.target.value)}
          >
            <option value="rural">Rural</option>
            <option value="urban">Urban</option>
          </select>
        </FormField>
      </div>

      {/* Financial */}
      <p className="form-section-title">Financial</p>
      <div className="form-grid">
        <FormField
          label="Annual family income (₹)"
          error={touched.family_income && errors.family_income}
        >
          <div className="input-prefix-wrapper">
            <span className="input-prefix">₹</span>
            <input
              id="field-income"
              type="number"
              min="0"
              value={form.family_income}
              onChange={(e) => update("family_income", e.target.value)}
              onBlur={() => touch("family_income")}
              placeholder="e.g. 50000"
              className={inputClass("family_income")}
            />
          </div>
        </FormField>
      </div>

      {/* Disability */}
      <div
        className="checkbox-field"
        onClick={() => update("disability", !form.disability)}
        role="presentation"
        tabIndex={-1}
      >
        <input
          id="field-disability"
          type="checkbox"
          checked={form.disability}
          onChange={(e) => update("disability", e.target.checked)}
          onClick={(e) => e.stopPropagation()}
        />
        <div>
          <div className="checkbox-field-label">I have a disability</div>
          <div className="checkbox-field-sub">
            Disability status unlocks additional assistive-device and welfare schemes
          </div>
        </div>
      </div>

      <button id="btn-find-schemes" className="submit-btn" type="submit" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner" />
            Finding your schemes…
          </>
        ) : (
          <>
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
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

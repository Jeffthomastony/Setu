import { useState, useMemo } from "react";

const EDUCATION_LEVELS = [
  "Class 1-5",
  "Class 6-7",
  "Class 8",
  "Class 9-10",
  "Class 11-12",
  "ITI",
  "Polytechnic/Diploma",
  "Undergraduate",
  "Postgraduate",
  "Professional",
  "Doctoral",
];

const CATEGORIES = ["General", "OBC", "SC", "ST", "OEC"];

const RELIGIONS = [
  { value: "hindu", label: "Hindu" },
  { value: "muslim", label: "Muslim" },
  { value: "christian", label: "Christian" },
  { value: "sikh", label: "Sikh" },
  { value: "buddhist", label: "Buddhist" },
  { value: "jain", label: "Jain" },
  { value: "parsi", label: "Parsi / Zoroastrian" },
  { value: "other", label: "Other" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

const INSTITUTION_TYPES = [
  { value: "Government", label: "Government (State / Central)" },
  { value: "Government-Aided", label: "Government-Aided" },
  { value: "Private Unaided", label: "Private Unaided (Self-financing)" },
  { value: "Minority Institution", label: "Minority Institution" },
  { value: "Open/Distance", label: "Open / Distance Learning" },
  { value: "Deemed University", label: "Deemed / Private University" },
];

// Complete list of Indian states and Union Territories
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
  education_level: "Undergraduate",
  academic_percentage: "",
  cgpa: "",
  parent_status: "both_parents",
  gender: "female",
  disability: false,
  religion: "prefer_not_to_say",
  institution_type: "Government",
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

export default function StudentForm({ onSubmit, loading }) {
  const [form, setForm] = useState(INITIAL_STATE);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [stateSearch, setStateSearch] = useState("");

  // Filtered states for the searchable dropdown
  const filteredStates = useMemo(
    () =>
      INDIAN_STATES.filter((s) =>
        s.toLowerCase().includes(stateSearch.toLowerCase())
      ),
    [stateSearch]
  );

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (touched[field]) validate({ ...form, [field]: value });
  }

  function touch(field) {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }

  function validate(values = form) {
    const errs = {};
    if (!values.age || Number(values.age) < 1 || Number(values.age) > 100)
      errs.age = "Enter a valid age (1–100)";
    if (values.family_income === "" || Number(values.family_income) < 0)
      errs.family_income = "Enter a valid annual income (₹)";
    if (!values.state.trim()) errs.state = "State is required";
    if (
      values.academic_percentage !== "" &&
      (Number(values.academic_percentage) < 0 ||
        Number(values.academic_percentage) > 100)
    )
      errs.academic_percentage = "Must be 0–100";
    if (
      values.cgpa !== "" &&
      (Number(values.cgpa) < 0 || Number(values.cgpa) > 10)
    )
      errs.cgpa = "Must be 0–10";
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
      education_level: form.education_level,
      academic_percentage:
        form.academic_percentage === "" ? null : Number(form.academic_percentage),
      cgpa: form.cgpa === "" ? null : Number(form.cgpa),
      parent_status: form.parent_status,
      gender: form.gender,
      disability: form.disability,
      religion: form.religion === "prefer_not_to_say" ? null : form.religion,
      institution_type: form.institution_type || null,
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
            min="1"
            max="100"
            value={form.age}
            onChange={(e) => update("age", e.target.value)}
            onBlur={() => touch("age")}
            placeholder="e.g. 19"
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

        <FormField label="Religion" hint="helps surface minority schemes">
          <select
            id="field-religion"
            value={form.religion}
            onChange={(e) => update("religion", e.target.value)}
          >
            {RELIGIONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
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

      {/* Education */}
      <p className="form-section-title">Education</p>
      <div className="form-grid">
        <FormField label="Current education level">
          <select
            id="field-education"
            value={form.education_level}
            onChange={(e) => update("education_level", e.target.value)}
          >
            {EDUCATION_LEVELS.map((lvl) => (
              <option key={lvl} value={lvl}>
                {lvl}
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Type of institution" hint="affects scheme eligibility">
          <select
            id="field-institution"
            value={form.institution_type}
            onChange={(e) => update("institution_type", e.target.value)}
          >
            {INSTITUTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </FormField>

        <FormField
          label="Academic percentage"
          hint="optional"
          error={touched.academic_percentage && errors.academic_percentage}
        >
          <input
            id="field-percentage"
            type="number"
            min="0"
            max="100"
            step="0.1"
            value={form.academic_percentage}
            onChange={(e) => update("academic_percentage", e.target.value)}
            onBlur={() => touch("academic_percentage")}
            placeholder="e.g. 78.5"
            className={inputClass("academic_percentage")}
          />
        </FormField>

        <FormField
          label="CGPA (out of 10)"
          hint="optional, if no % given"
          error={touched.cgpa && errors.cgpa}
        >
          <input
            id="field-cgpa"
            type="number"
            min="0"
            max="10"
            step="0.1"
            value={form.cgpa}
            onChange={(e) => update("cgpa", e.target.value)}
            onBlur={() => touch("cgpa")}
            placeholder="e.g. 8.2"
            className={inputClass("cgpa")}
          />
        </FormField>
      </div>

      {/* Financial & Family */}
      <p className="form-section-title">Financial &amp; Family</p>
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
              placeholder="e.g. 80000"
              className={inputClass("family_income")}
            />
          </div>
        </FormField>

        <FormField label="Parent status">
          <select
            id="field-parent"
            value={form.parent_status}
            onChange={(e) => update("parent_status", e.target.value)}
          >
            <option value="both_parents">Both parents alive</option>
            <option value="single_parent">Single parent</option>
            <option value="orphan">Orphan (both parents deceased)</option>
          </select>
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
            Disability status unlocks additional reserved and welfare schemes
          </div>
        </div>
      </div>

      <button id="btn-find-schemes" className="submit-btn" type="submit" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner" />
            Finding your scholarships…
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
            Find My Scholarships
          </>
        )}
      </button>
    </form>
  );
}

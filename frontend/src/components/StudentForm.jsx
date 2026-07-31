import { useState } from "react";

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
};

export default function StudentForm({ onSubmit, loading }) {
  const [form, setForm] = useState(INITIAL_STATE);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();

    const payload = {
      age: Number(form.age),
      family_income: Number(form.family_income),
      category: form.category,
      state: form.state.trim(),
      residence_area: form.residence_area,
      education_level: form.education_level,
      academic_percentage: form.academic_percentage === "" ? null : Number(form.academic_percentage),
      cgpa: form.cgpa === "" ? null : Number(form.cgpa),
      parent_status: form.parent_status,
      gender: form.gender,
      disability: form.disability,
    };

    onSubmit(payload);
  }

  return (
    <form className="student-form" onSubmit={handleSubmit}>
      <p className="privacy-note">
        Your details are used only to compute matches for this session and are never saved or sent anywhere else.
      </p>

      <div className="form-grid">
        <label>
          Age
          <input
            type="number"
            required
            min="1"
            max="100"
            value={form.age}
            onChange={(e) => update("age", e.target.value)}
          />
        </label>

        <label>
          Annual family income (₹)
          <input
            type="number"
            required
            min="0"
            value={form.family_income}
            onChange={(e) => update("family_income", e.target.value)}
          />
        </label>

        <label>
          Category
          <select value={form.category} onChange={(e) => update("category", e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        <label>
          State
          <input type="text" required value={form.state} onChange={(e) => update("state", e.target.value)} />
        </label>

        <label>
          Residence area
          <select value={form.residence_area} onChange={(e) => update("residence_area", e.target.value)}>
            <option value="rural">Rural</option>
            <option value="urban">Urban</option>
          </select>
        </label>

        <label>
          Current education level
          <select value={form.education_level} onChange={(e) => update("education_level", e.target.value)}>
            {EDUCATION_LEVELS.map((lvl) => (
              <option key={lvl} value={lvl}>
                {lvl}
              </option>
            ))}
          </select>
        </label>

        <label>
          Academic percentage (optional)
          <input
            type="number"
            min="0"
            max="100"
            step="0.1"
            value={form.academic_percentage}
            onChange={(e) => update("academic_percentage", e.target.value)}
            placeholder="e.g. 78"
          />
        </label>

        <label>
          CGPA out of 10 (optional, used if no percentage given)
          <input
            type="number"
            min="0"
            max="10"
            step="0.1"
            value={form.cgpa}
            onChange={(e) => update("cgpa", e.target.value)}
            placeholder="e.g. 8.2"
          />
        </label>

        <label>
          Parent status
          <select value={form.parent_status} onChange={(e) => update("parent_status", e.target.value)}>
            <option value="both_parents">Both parents</option>
            <option value="single_parent">Single parent</option>
            <option value="orphan">Orphan</option>
          </select>
        </label>

        <label>
          Gender
          <select value={form.gender} onChange={(e) => update("gender", e.target.value)}>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={form.disability}
            onChange={(e) => update("disability", e.target.checked)}
          />
          I have a disability
        </label>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? "Finding matches..." : "Find my schemes"}
      </button>
    </form>
  );
}

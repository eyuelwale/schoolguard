import React, { useEffect, useState } from "react";
import {
  Bell, CalendarCheck2, CheckCircle2, Clock3, LayoutDashboard,
  LogOut, Menu, Search, ShieldCheck, Users, UserRound, X, Plus,
  Building2, GraduationCap, Link2, Send, Settings, UserPlus, Eye,
  Sparkles, RefreshCw, AlertTriangle, UserCheck, Pencil, Trash2, Unlink, RotateCcw
} from "lucide-react";
import api from "./api";

/* Helper to safely extract error message from API response without crashing React */
function getApiErrorMessage(err, fallback = "An unexpected error occurred") {
  const detail = err?.response?.data?.detail;
  if (!detail) return err?.message || fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        const field = item?.loc ? item.loc.filter((x) => x !== "body").join(".") : "";
        return field ? `${field}: ${item.msg}` : item.msg || JSON.stringify(item);
      })
      .join("; ");
  }
  if (typeof detail === "object") {
    return detail.msg || JSON.stringify(detail);
  }
  return String(detail);
}

/*  Navigation Items  */
const navItems = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "schools", label: "Schools", icon: Building2 },
  { key: "classes", label: "Classes", icon: GraduationCap },
  { key: "teachers", label: "Teachers", icon: UserCheck },
  { key: "students", label: "Students", icon: Users },
  { key: "attendance", label: "Attendance", icon: CalendarCheck2 },
  { key: "parents", label: "Parents & Links", icon: UserRound },
  { key: "users", label: "User Accounts", icon: ShieldCheck },
  { key: "notifications", label: "Notifications & Logs", icon: Bell },
];

/*  Alert Banner (Success / Error)  */
function AlertBanner({ feedback, onClose }) {
  if (!feedback) return null;
  const data = typeof feedback === "string" ? { type: "success", message: feedback } : feedback;
  if (!data || !data.message) return null;
  const isSuccess = data.type !== "error";
  const displayMsg = typeof data.message === "string"
    ? data.message
    : (Array.isArray(data.message) ? data.message.map(m => m?.msg || JSON.stringify(m)).join("; ") : JSON.stringify(data.message));
  return (
    <div
      className={isSuccess ? "modal-success" : "error"}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        marginBottom: 16,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {isSuccess ? <CheckCircle2 size={18} color="#059669" /> : <AlertTriangle size={18} color="#dc2626" />}
        <span style={{ fontWeight: 600 }}>{displayMsg}</span>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            background: "none",
            border: "none",
            color: "inherit",
            cursor: "pointer",
            padding: "2px 4px",
            opacity: 0.7,
            display: "flex",
            alignItems: "center",
          }}
          title="Dismiss"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}

/*  Reusable Modal  */
function Modal({ title, onClose, children, large }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className={`modal-card ${large ? "large" : ""}`} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

/*  Confirm Deletion Modal  */
function ConfirmModal({ title = "Confirm Deletion", message, onConfirm, onClose, loading }) {
  return (
    <Modal title={title} onClose={onClose}>
      <div className="confirm-box">
        <div className="confirm-icon">
          <AlertTriangle size={26} />
        </div>
        <p style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600, color: "var(--foreground)" }}>
          {message || "Are you sure you want to delete this record?"}
        </p>
        <p style={{ margin: 0, fontSize: 13, color: "var(--muted)" }}>
          This action cannot be undone. Dependent links will be automatically cleaned up.
        </p>
        <div className="confirm-actions">
          <button type="button" className="secondary" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-sm-danger"
            style={{
              justifyContent: "center",
              padding: "10px 16px",
              background: "#ef4444",
              color: "#ffffff",
              border: "1px solid #dc2626",
              borderRadius: 8,
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer"
            }}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? "Deleting..." : "Delete Permanently"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

/*  Edit School Modal  */
function EditSchoolModal({ school, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: school.name || "",
    code: school.code || "",
    address: school.address || "",
    phone: school.phone || "",
    status: school.status || "ACTIVE"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        name: form.name?.trim(),
        code: form.code?.trim(),
        address: form.address?.trim() || null,
        phone: form.phone?.trim() || null,
        status: form.status,
      };
      await api.put(`/api/schools/${school.id}`, payload);
      onSaved(`School "${form.name}" updated successfully`);
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to update school"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Edit School" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          School Name *
          <input value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </label>
        <label>
          School Code *
          <input value={form.code} onChange={(e) => set("code", e.target.value)} required />
        </label>
        <label>
          Address
          <input value={form.address} onChange={(e) => set("address", e.target.value)} />
        </label>
        <label>
          Phone
          <input value={form.phone} onChange={(e) => set("phone", e.target.value)} />
        </label>
        <label>
          Status
          <select value={form.status} onChange={(e) => set("status", e.target.value)}>
            <option value="ACTIVE">ACTIVE</option>
            <option value="INACTIVE">INACTIVE</option>
          </select>
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Saving..." : "Save Changes"}</button>
      </form>
    </Modal>
  );
}

/*  Edit Class Modal  */
function EditClassModal({ cls, schools, onClose, onSaved }) {
  const [form, setForm] = useState({
    school_id: cls.school_id,
    class_code: cls.class_code || "",
    class_name: cls.class_name || "",
    grade: cls.grade || "",
    section: cls.section || "",
    academic_year: cls.academic_year || "2025-2026",
    school_start_time: cls.school_start_time || "08:00:00",
    school_end_time: cls.school_end_time || "15:30:00",
    status: cls.status || "ACTIVE"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        school_id: Number(form.school_id),
        class_code: form.class_code?.trim(),
        class_name: form.class_name?.trim(),
        grade: form.grade?.trim(),
        section: form.section?.trim() || null,
        academic_year: form.academic_year?.trim(),
        school_start_time: form.school_start_time?.trim() || null,
        school_end_time: form.school_end_time?.trim() || null,
        status: form.status,
      };
      await api.put(`/api/classes/${cls.id}`, payload);
      onSaved(`Class "${form.class_name}" updated successfully`);
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to update class"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Edit Class" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          School
          <select value={form.school_id} onChange={(e) => set("school_id", Number(e.target.value))}>
            {schools.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
          </select>
        </label>
        <label>
          Class Code *
          <input value={form.class_code} onChange={(e) => set("class_code", e.target.value)} required />
        </label>
        <label>
          Class Name *
          <input value={form.class_name} onChange={(e) => set("class_name", e.target.value)} required />
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label>
            Grade *
            <input value={form.grade} onChange={(e) => set("grade", e.target.value)} required />
          </label>
          <label>
            Section
            <input value={form.section} onChange={(e) => set("section", e.target.value)} />
          </label>
        </div>
        <label>
          Academic Year *
          <input value={form.academic_year} onChange={(e) => set("academic_year", e.target.value)} required />
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label>
            Start Time
            <input type="time" step="1" value={form.school_start_time?.slice(0, 5) || "08:00"} onChange={(e) => set("school_start_time", e.target.value + ":00")} />
          </label>
          <label>
            End Time
            <input type="time" step="1" value={form.school_end_time?.slice(0, 5) || "15:30"} onChange={(e) => set("school_end_time", e.target.value + ":00")} />
          </label>
        </div>
        <label>
          Status
          <select value={form.status} onChange={(e) => set("status", e.target.value)}>
            <option value="ACTIVE">ACTIVE</option>
            <option value="INACTIVE">INACTIVE</option>
          </select>
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Saving..." : "Save Changes"}</button>
      </form>
    </Modal>
  );
}

/*  Edit Student Modal  */
function EditStudentModal({ student, schools, classes, onClose, onSaved }) {
  const [form, setForm] = useState({
    school_id: student.school_id,
    class_id: student.class_id || "",
    student_code: student.student_code || "",
    first_name: student.first_name || "",
    middle_name: student.middle_name || "",
    last_name: student.last_name || "",
    gender: student.gender || "MALE",
    date_of_birth: student.date_of_birth || "",
    status: student.status || "ACTIVE"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        school_id: Number(form.school_id),
        class_id: form.class_id ? Number(form.class_id) : null,
        student_code: form.student_code?.trim(),
        first_name: form.first_name?.trim(),
        middle_name: form.middle_name?.trim() || null,
        last_name: form.last_name?.trim() || null,
        gender: form.gender,
        date_of_birth: form.date_of_birth?.trim() || null,
        status: form.status,
      };
      await api.put(`/api/students/${student.id}`, payload);
      onSaved(`Student "${[form.first_name, form.last_name].filter(Boolean).join(" ")}" updated successfully`);
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to update student"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Edit Student Profile" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          School
          <select value={form.school_id} onChange={(e) => set("school_id", Number(e.target.value))}>
            {schools.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </label>
        <label>
          Class Assignment
          <select value={form.class_id} onChange={(e) => set("class_id", e.target.value)}>
            <option value="">-- Unassigned --</option>
            {classes.map((c) => <option key={c.id} value={c.id}>{c.class_name} ({c.class_code})</option>)}
          </select>
        </label>
        <label>
          Student Code *
          <input value={form.student_code} onChange={(e) => set("student_code", e.target.value)} required />
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
          <label>
            First Name *
            <input value={form.first_name} onChange={(e) => set("first_name", e.target.value)} required />
          </label>
          <label>
            Middle Name
            <input value={form.middle_name} onChange={(e) => set("middle_name", e.target.value)} />
          </label>
          <label>
            Last Name
            <input value={form.last_name} onChange={(e) => set("last_name", e.target.value)} />
          </label>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label>
            Gender
            <select value={form.gender} onChange={(e) => set("gender", e.target.value)}>
              <option value="MALE">Male</option>
              <option value="FEMALE">Female</option>
            </select>
          </label>
          <label>
            Date of Birth
            <input type="date" value={form.date_of_birth} onChange={(e) => set("date_of_birth", e.target.value)} />
          </label>
        </div>
        <label>
          Status
          <select value={form.status} onChange={(e) => set("status", e.target.value)}>
            <option value="ACTIVE">ACTIVE</option>
            <option value="INACTIVE">INACTIVE</option>
            <option value="GRADUATED">GRADUATED</option>
            <option value="TRANSFERRED">TRANSFERRED</option>
          </select>
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Saving..." : "Save Changes"}</button>
      </form>
    </Modal>
  );
}

/*  Edit User Modal (Users, Teachers, and Parents)  */
function EditUserModal({ user, onClose, onSaved }) {
  const roleLabel = user.role === "TEACHER" ? "Teacher" : user.role === "PARENT" ? "Parent" : "User";
  const [form, setForm] = useState({
    full_name: user.full_name || "",
    email: user.email || "",
    phone: user.phone || "",
    role: user.role || "PARENT",
    status: user.status || "ACTIVE",
    password: "",
    telegram_id: user.telegram_id ? String(user.telegram_id) : "",
    telegram_username: user.telegram_username || "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        full_name: form.full_name?.trim(),
        email: form.email?.trim() || null,
        phone: form.phone?.trim() || null,
        role: form.role,
        status: form.status,
        telegram_id: form.telegram_id && String(form.telegram_id).trim() ? Number(String(form.telegram_id).trim()) : null,
        telegram_username: form.telegram_username?.trim() || null,
      };
      if (form.password && form.password.trim()) {
        payload.password = form.password.trim();
      }
      await api.put(`/api/users/${user.id}`, payload);
      onSaved(`${roleLabel} "${form.full_name}" updated successfully`);
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, `Failed to update ${roleLabel.toLowerCase()}`));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title={`Edit ${roleLabel} Account`} onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Full Name *
          <input value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required />
        </label>
        <label>
          Email Address
          <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} />
        </label>
        <label>
          Phone Number
          <input value={form.phone} onChange={(e) => set("phone", e.target.value)} />
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label>
            Role
            <select value={form.role} onChange={(e) => set("role", e.target.value)}>
              <option value="ADMIN">ADMIN</option>
              <option value="TEACHER">TEACHER</option>
              <option value="PARENT">PARENT</option>
              <option value="SECURITY">SECURITY</option>
            </select>
          </label>
          <label>
            Status
            <select value={form.status} onChange={(e) => set("status", e.target.value)}>
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE</option>
              <option value="SUSPENDED">SUSPENDED</option>
            </select>
          </label>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label>
            Telegram User ID
            <input value={form.telegram_id} onChange={(e) => set("telegram_id", e.target.value)} />
          </label>
          <label>
            Telegram @Username
            <input value={form.telegram_username} onChange={(e) => set("telegram_username", e.target.value)} />
          </label>
        </div>
        <label>
          New Password (leave blank to keep current)
          <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Saving..." : "Save Changes"}</button>
      </form>
    </Modal>
  );
}

/*  Edit Attendance Record Modal  */
function EditAttendanceModal({ record, studentName, onClose, onSaved }) {
  const toLocalInput = (dt) => {
    if (!dt) return "";
    const d = new Date(dt);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  const [form, setForm] = useState({
    status: record.status || "PRESENT",
    arrival_time: toLocalInput(record.arrival_time),
    departure_time: toLocalInput(record.departure_time),
    arrival_method: record.arrival_method || "TEACHER",
    departure_method: record.departure_method || "TEACHER",
    notes: record.notes || "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        status: form.status,
        arrival_time: form.arrival_time ? new Date(form.arrival_time).toISOString() : null,
        departure_time: form.departure_time ? new Date(form.departure_time).toISOString() : null,
        arrival_method: form.arrival_method || null,
        departure_method: form.departure_method || null,
        notes: form.notes?.trim() || null,
      };
      await api.put(`/api/attendance/${record.id}`, payload);
      onSaved(`Attendance for ${studentName || "student"} updated successfully`);
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to update attendance record"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title={`Edit Attendance - ${studentName || `Record #${record.id}`}`} onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Attendance Status
          <select value={form.status} onChange={(e) => set("status", e.target.value)}>
            <option value="PRESENT">Present</option>
            <option value="LATE">Late</option>
            <option value="ABSENT">Absent</option>
            <option value="EXCUSED">Excused</option>
          </select>
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label>
            Arrival Timestamp
            <input type="datetime-local" value={form.arrival_time} onChange={(e) => set("arrival_time", e.target.value)} />
          </label>
          <label>
            Arrival Method
            <select value={form.arrival_method} onChange={(e) => set("arrival_method", e.target.value)}>
              <option value="TEACHER">Teacher</option>
              <option value="QR_SCAN">QR Scan</option>
              <option value="SECURITY">Security</option>
              <option value="MANUAL">Manual</option>
            </select>
          </label>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label>
            Departure Timestamp
            <input type="datetime-local" value={form.departure_time} onChange={(e) => set("departure_time", e.target.value)} />
          </label>
          <label>
            Departure Method
            <select value={form.departure_method} onChange={(e) => set("departure_method", e.target.value)}>
              <option value="TEACHER">Teacher</option>
              <option value="QR_SCAN">QR Scan</option>
              <option value="SECURITY">Security</option>
              <option value="MANUAL">Manual</option>
            </select>
          </label>
        </div>
        <label>
          Notes
          <input value={form.notes} onChange={(e) => set("notes", e.target.value)} />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Saving..." : "Update Attendance"}</button>
      </form>
    </Modal>
  );
}

/*  Edit Parent Link Modal  */
function EditParentLinkModal({ link, onClose, onSaved }) {
  const [form, setForm] = useState({
    relationship_type: link.relationship_type || "PARENT",
    is_primary: Boolean(link.is_primary),
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.put(`/api/parents/links/${link.id}`, form);
      onSaved(`Guardian link for "${link.student_name}" updated successfully`);
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to update link"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title={`Edit Link: ${link.parent_name} → ${link.student_name}`} onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Relationship Type
          <select value={form.relationship_type} onChange={(e) => setForm((f) => ({ ...f, relationship_type: e.target.value }))}>
            <option value="MOTHER">Mother</option>
            <option value="FATHER">Father</option>
            <option value="GUARDIAN">Guardian</option>
            <option value="PARENT">Parent</option>
            <option value="OTHER">Other</option>
          </select>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginTop: 8 }}>
          <input
            type="checkbox"
            checked={form.is_primary}
            onChange={(e) => setForm((f) => ({ ...f, is_primary: e.target.checked }))}
            style={{ width: "auto", margin: 0 }}
          />
          <strong>Primary Emergency Contact</strong>
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Saving..." : "Save Link"}</button>
      </form>
    </Modal>
  );
}

/* 
   MODALS: SCHOOLS & CLASSES
    */

/*  Add School Modal  */
function AddSchoolModal({ onClose, onSaved }) {
  const [form, setForm] = useState({ name: "", code: "", address: "", phone: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/api/schools/", form);
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create school");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Add New School" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          School Name *
          <input value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </label>
        <label>
          School Code *
          <input value={form.code} onChange={(e) => set("code", e.target.value)} required />
        </label>
        <label>
          Address
          <input value={form.address} onChange={(e) => set("address", e.target.value)} />
        </label>
        <label>
          Phone
          <input value={form.phone} onChange={(e) => set("phone", e.target.value)} />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Saving" : "Create School"}</button>
      </form>
    </Modal>
  );
}

/*  Add Class Modal  */
function AddClassModal({ schools, onClose, onSaved }) {
  const [form, setForm] = useState({
    school_id: schools[0]?.id || "",
    class_code: "",
    class_name: "",
    grade: "",
    section: "",
    academic_year: "2025-2026",
    school_start_time: "08:00:00",
    school_end_time: "15:30:00"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/api/classes/", { ...form, school_id: parseInt(form.school_id) });
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create class");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Add New Class" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          School *
          <select value={form.school_id} onChange={(e) => set("school_id", e.target.value)} required>
            <option value="">Select School</option>
            {schools.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
          </select>
        </label>
        <div className="form-row">
          <label>
            Class Name *
            <input value={form.class_name} onChange={(e) => set("class_name", e.target.value)} required />
          </label>
          <label>
            Class Code *
            <input value={form.class_code} onChange={(e) => set("class_code", e.target.value)} required />
          </label>
        </div>
        <div className="form-row">
          <label>
            Grade *
            <input value={form.grade} onChange={(e) => set("grade", e.target.value)} required />
          </label>
          <label>
            Section
            <input value={form.section} onChange={(e) => set("section", e.target.value)} />
          </label>
        </div>
        <label>
          Academic Year *
          <input value={form.academic_year} onChange={(e) => set("academic_year", e.target.value)} required />
        </label>
        <div className="form-row">
          <label>
            Start Time
            <input type="time" value={form.school_start_time?.slice(0, 5)} onChange={(e) => set("school_start_time", e.target.value ? `${e.target.value}:00` : null)} />
          </label>
          <label>
            End Time
            <input type="time" value={form.school_end_time?.slice(0, 5)} onChange={(e) => set("school_end_time", e.target.value ? `${e.target.value}:00` : null)} />
          </label>
        </div>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading || !form.school_id}>{loading ? "Saving" : "Create Class"}</button>
      </form>
    </Modal>
  );
}

/*  Add Teacher Modal  */
function AddTeacherModal({ classes = [], onClose, onSaved }) {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    password: "Teacher123!",
    class_id: classes[0]?.id || "",
    academic_year: "2025-2026",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/api/auth/register", {
        full_name: form.full_name,
        email: form.email,
        phone: form.phone || null,
        password: form.password,
        role: "TEACHER",
      });
      const newTeacherId = res.data.id;
      // If a class was selected, assign the teacher to the class right away
      if (form.class_id && newTeacherId) {
        try {
          await api.post("/api/classes/assign-teacher", {
            class_id: parseInt(form.class_id),
            teacher_id: newTeacherId,
            academic_year: form.academic_year || "2025-2026",
          });
        } catch (assignErr) {
          console.warn("Teacher created, assignment skipped/duplicate:", assignErr);
        }
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add teacher");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Add New Teacher" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Teacher Full Name *
          <input
            value={form.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            required
          />
        </label>
        <div className="form-row">
          <label>
            Email Address *
            <input
              type="email"
              value={form.email}
              onChange={(e) => set("email", e.target.value)}
              required
            />
          </label>
          <label>
            Phone Number
            <input
              value={form.phone}
              onChange={(e) => set("phone", e.target.value)}
            />
          </label>
        </div>
        <div className="form-row">
          <label>
            Initial Password *
            <input
              type="password"
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
              required
            />
          </label>
          <label>
            Assign to Class (Optional)
            <select value={form.class_id} onChange={(e) => set("class_id", e.target.value)}>
              <option value="">Do not assign yet</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.class_name} ({c.class_code})
                </option>
              ))}
            </select>
          </label>
        </div>
        {form.class_id && (
          <label>
            Academic Year
            <input
              value={form.academic_year}
              onChange={(e) => set("academic_year", e.target.value)}
            />
          </label>
        )}
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>
          {loading ? "Saving..." : "Create Teacher Account"}
        </button>
      </form>
    </Modal>
  );
}

/*  Assign Teacher to Class Modal  */
function AssignTeacherModal({ classes, teachers, initialTeacherId, onClose, onSaved, onOpenAddTeacher }) {
  const [form, setForm] = useState({
    class_id: classes[0]?.id || "",
    teacher_id: initialTeacherId || teachers[0]?.id || "",
    academic_year: "2025-2026"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/api/classes/assign-teacher", {
        class_id: parseInt(form.class_id),
        teacher_id: parseInt(form.teacher_id),
        academic_year: form.academic_year
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to assign teacher");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Assign Teacher to Class" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Select Class *
          <select value={form.class_id} onChange={(e) => set("class_id", e.target.value)} required>
            <option value="">Select Class</option>
            {classes.map((c) => <option key={c.id} value={c.id}>{c.class_name} ({c.class_code})</option>)}
          </select>
        </label>
        <label>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>Select Teacher *</span>
            {onOpenAddTeacher && (
              <button
                type="button"
                onClick={onOpenAddTeacher}
                style={{ background: "none", border: "none", color: "#4f46e5", fontSize: 12, cursor: "pointer", fontWeight: 600, padding: 0 }}
              >
                + Add New Teacher
              </button>
            )}
          </div>
          <select value={form.teacher_id} onChange={(e) => set("teacher_id", e.target.value)} required>
            <option value="">Select Teacher</option>
            {teachers.map((t) => <option key={t.id} value={t.id}>{t.full_name} ({t.email})</option>)}
          </select>
        </label>
        {teachers.length === 0 && (
          <div style={{ background: "#fffbeb", border: "1px solid #fde68a", padding: "10px 14px", borderRadius: 8, fontSize: 13, color: "#92400e" }}>
            No teachers registered yet. Please add a teacher account first.
          </div>
        )}
        <label>
          Academic Year *
          <input value={form.academic_year} onChange={(e) => set("academic_year", e.target.value)} required />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading || !form.class_id || !form.teacher_id}>{loading ? "Saving" : "Assign Teacher"}</button>
      </form>
    </Modal>
  );
}

/* 
   MODALS: STUDENTS & ATTENDANCE
    */

/*  Add Student Modal  */
function AddStudentModal({ schools, classes, onClose, onSaved }) {
  const [form, setForm] = useState({
    school_id: schools[0]?.id || "",
    class_id: "",
    student_code: "",
    first_name: "",
    middle_name: "",
    last_name: "",
    gender: "MALE",
    date_of_birth: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/api/students/", {
        ...form,
        school_id: parseInt(form.school_id),
        class_id: form.class_id ? parseInt(form.class_id) : null,
        date_of_birth: form.date_of_birth || null
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add student");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Add New Student" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <div className="form-row">
          <label>
            School *
            <select value={form.school_id} onChange={(e) => set("school_id", e.target.value)} required>
              <option value="">Select school</option>
              {schools.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </label>
          <label>
            Assigned Class
            <select value={form.class_id} onChange={(e) => set("class_id", e.target.value)}>
              <option value="">Unassigned</option>
              {classes.map((c) => <option key={c.id} value={c.id}>{c.class_name}</option>)}
            </select>
          </label>
        </div>
        <label>
          Student Code *
          <input value={form.student_code} onChange={(e) => set("student_code", e.target.value)} required />
        </label>
        <div className="form-row">
          <label>
            First Name *
            <input value={form.first_name} onChange={(e) => set("first_name", e.target.value)} required />
          </label>
          <label>
            Middle Name
            <input value={form.middle_name} onChange={(e) => set("middle_name", e.target.value)} />
          </label>
        </div>
        <div className="form-row">
          <label>
            Last Name
            <input value={form.last_name} onChange={(e) => set("last_name", e.target.value)} />
          </label>
          <label>
            Gender
            <select value={form.gender} onChange={(e) => set("gender", e.target.value)}>
              <option value="MALE">Male</option>
              <option value="FEMALE">Female</option>
            </select>
          </label>
        </div>
        <label>
          Date of Birth
          <input type="date" value={form.date_of_birth} onChange={(e) => set("date_of_birth", e.target.value)} />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading || !form.school_id}>{loading ? "Saving" : "Save Student"}</button>
      </form>
    </Modal>
  );
}

/*  Student Details & History Modal  */
function StudentDetailsModal({ studentId, onClose }) {
  const [student, setStudent] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get(`/api/students/${studentId}`).then((r) => r.data),
      api.get(`/api/attendance/student/${studentId}`).then((r) => r.data).catch(() => [])
    ])
      .then(([s, h]) => {
        setStudent(s);
        setHistory(h);
      })
      .finally(() => setLoading(false));
  }, [studentId]);

  return (
    <Modal title="Student Details & Attendance" onClose={onClose} large>
      {loading ? (
        <div className="empty">Loading student records</div>
      ) : !student ? (
        <div className="empty">Student not found</div>
      ) : (
        <div>
          <div className="panel-head" style={{ marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 20 }}>
                {[student.first_name, student.middle_name, student.last_name].filter(Boolean).join(" ")}
              </h3>
              <p>Code: <strong>{student.student_code}</strong> | Gender: {student.gender || ""} | DOB: {student.date_of_birth || ""}</p>
            </div>
            <span className="pill success">{student.status}</span>
          </div>

          <div style={{ background: "#f8fafc", padding: "12px 16px", borderRadius: 12, marginBottom: 20, border: "1px solid #e2e8f0" }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Security QR Token</div>
            <code style={{ wordBreak: "break-all", fontSize: 12, color: "#4f46e5" }}>{student.qr_token || "None generated"}</code>
          </div>

          <h4>Attendance History (Last 100 Days)</h4>
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Arrival</th>
                  <th>Departure</th>
                  <th>Status</th>
                  <th>Method</th>
                </tr>
              </thead>
              <tbody>
                {history.map((r) => (
                  <tr key={r.id}>
                    <td><strong>{r.attendance_date}</strong></td>
                    <td>{r.arrival_time ? new Date(r.arrival_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}</td>
                    <td>{r.departure_time ? new Date(r.departure_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}</td>
                    <td><span className={`status ${r.status?.toLowerCase()}`}>{r.status}</span></td>
                    <td>{r.arrival_method || ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!history.length && <div className="empty">No past attendance logs found for this student.</div>}
          </div>
        </div>
      )}
    </Modal>
  );
}

/*  Record Attendance Modal  */
function AddAttendanceModal({ students, onClose, onSaved }) {
  const [form, setForm] = useState({ student_id: students[0]?.id || "", type: "ARRIVAL", method: "TEACHER", status: "PRESENT" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const id = parseInt(form.student_id);
      if (form.type === "ARRIVAL") {
        await api.post("/api/attendance/arrival", { student_id: id, method: form.method });
      } else if (form.type === "DEPARTURE") {
        await api.post("/api/attendance/departure", { student_id: id, method: form.method });
      } else {
        await api.put("/api/attendance/status", { student_id: id, status: form.status });
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to record attendance");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Record Student Attendance" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Student *
          <select value={form.student_id} onChange={(e) => set("student_id", e.target.value)} required>
            <option value="">Select student</option>
            {students.map((s) => (
              <option key={s.id} value={s.id}>
                {[s.first_name, s.middle_name, s.last_name].filter(Boolean).join(" ")} ({s.student_code})
              </option>
            ))}
          </select>
        </label>
        <label>
          Action Type *
          <select value={form.type} onChange={(e) => set("type", e.target.value)}>
            <option value="ARRIVAL"> Mark Arrival (Check-in)</option>
            <option value="DEPARTURE"> Mark Departure (Check-out)</option>
            <option value="STATUS"> Set Direct Status (Present/Late/Absent/Excused)</option>
          </select>
        </label>
        {form.type !== "STATUS" ? (
          <label>
            Method
            <select value={form.method} onChange={(e) => set("method", e.target.value)}>
              <option value="TEACHER">Teacher Check</option>
              <option value="SECURITY">Security Gate Scanner</option>
              <option value="RFID">RFID Card</option>
              <option value="BIOMETRIC">Biometric Scan</option>
            </select>
          </label>
        ) : (
          <label>
            Status
            <select value={form.status} onChange={(e) => set("status", e.target.value)}>
              <option value="PRESENT">Present</option>
              <option value="LATE">Late</option>
              <option value="ABSENT">Absent</option>
              <option value="EXCUSED">Excused</option>
            </select>
          </label>
        )}
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading || !form.student_id}>{loading ? "Saving" : "Submit Attendance"}</button>
      </form>
    </Modal>
  );
}

/* 
   MODALS: USERS, PARENTS & TELEGRAM
    */

/*  Create User Modal  */
function CreateUserModal({ onClose, onSaved }) {
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", password: "", role: "TEACHER" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/api/auth/register", form);
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to register user");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Register New User" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Full Name *
          <input value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required />
        </label>
        <div className="form-row">
          <label>
            Email *
            <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
          </label>
          <label>
            Phone
            <input value={form.phone} onChange={(e) => set("phone", e.target.value)} />
          </label>
        </div>
        <div className="form-row">
          <label>
            Role *
            <select value={form.role} onChange={(e) => set("role", e.target.value)}>
              <option value="TEACHER">Teacher</option>
              <option value="PARENT">Parent</option>
              <option value="SECURITY">Security Staff</option>
            </select>
          </label>
          <label>
            Password *
            <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required />
          </label>
        </div>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Saving" : "Register User"}</button>
      </form>
    </Modal>
  );
}

/*  Link Student to Parent Modal  */
function LinkStudentModal({ parents, students, onClose, onSaved }) {
  const [form, setForm] = useState({
    parent_id: parents[0]?.id || "",
    student_id: students[0]?.id || "",
    relationship_type: "PARENT",
    is_primary: true
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/api/parents/link-student", {
        parent_id: parseInt(form.parent_id),
        student_id: parseInt(form.student_id),
        relationship_type: form.relationship_type,
        is_primary: form.is_primary
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to link student to parent");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Link Student to Parent" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Select Parent *
          <select value={form.parent_id} onChange={(e) => set("parent_id", e.target.value)} required>
            <option value="">Select Parent</option>
            {parents.map((p) => <option key={p.id} value={p.id}>{p.full_name} ({p.email || p.phone || "No contact"})</option>)}
          </select>
        </label>
        <label>
          Select Student *
          <select value={form.student_id} onChange={(e) => set("student_id", e.target.value)} required>
            <option value="">Select Student</option>
            {students.map((s) => (
              <option key={s.id} value={s.id}>
                {[s.first_name, s.middle_name, s.last_name].filter(Boolean).join(" ")} ({s.student_code})
              </option>
            ))}
          </select>
        </label>
        <div className="form-row">
          <label>
            Relationship Type
            <select value={form.relationship_type} onChange={(e) => set("relationship_type", e.target.value)}>
              <option value="PARENT">Parent</option>
              <option value="FATHER">Father</option>
              <option value="MOTHER">Mother</option>
              <option value="GUARDIAN">Guardian</option>
            </select>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 24 }}>
            <input
              type="checkbox"
              style={{ width: "auto", margin: 0 }}
              checked={form.is_primary}
              onChange={(e) => set("is_primary", e.target.checked)}
            />
            Primary Contact
          </label>
        </div>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading || !form.parent_id || !form.student_id}>{loading ? "Saving" : "Link Student"}</button>
      </form>
    </Modal>
  );
}

/*  Link Telegram Account Modal (Admin action)  */
function LinkTelegramModal({ parent, onClose, onSaved }) {
  const [form, setForm] = useState({ telegram_id: parent?.telegram_id || "", telegram_username: parent?.telegram_username || "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post(`/api/telegram/link?parent_id=${parent.id}`, {
        telegram_id: parseInt(form.telegram_id),
        telegram_username: form.telegram_username ? form.telegram_username.replace("@", "") : null
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to link Telegram");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title={`Link Telegram: ${parent.full_name}`} onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <p style={{ fontSize: 13, color: "#64748b", margin: "0 0 16px" }}>
          Assign the Telegram numeric ID & username for this parent to receive push alerts.
        </p>
        <label>
          Telegram ID (Numeric) *
          <input
            type="number"
            value={form.telegram_id}
            onChange={(e) => set("telegram_id", e.target.value)}
            required
          />
        </label>
        <label>
          Telegram Username (Optional)
          <input
            value={form.telegram_username}
            onChange={(e) => set("telegram_username", e.target.value)}
          />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading || !form.telegram_id}>{loading ? "Saving" : "Save Telegram Link"}</button>
      </form>
    </Modal>
  );
}

/*  Self Link Telegram Modal  */
function SelfLinkTelegramModal({ currentUser, onClose, onSaved }) {
  const [form, setForm] = useState({ telegram_id: currentUser?.telegram_id || "", telegram_username: currentUser?.telegram_username || "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/api/telegram/link-self", {
        telegram_id: parseInt(form.telegram_id),
        telegram_username: form.telegram_username ? form.telegram_username.replace("@", "") : null
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to link Telegram account");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Link Your Personal Telegram" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Your Telegram Numeric ID *
          <input
            type="number"
            value={form.telegram_id}
            onChange={(e) => set("telegram_id", e.target.value)}
            required
          />
        </label>
        <label>
          Your Telegram Username
          <input
            value={form.telegram_username}
            onChange={(e) => set("telegram_username", e.target.value)}
          />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading || !form.telegram_id}>{loading ? "Saving" : "Link Account"}</button>
      </form>
    </Modal>
  );
}

/*  Notification Settings Modal  */
function NotificationSettingsModal({ students, onClose }) {
  const [form, setForm] = useState({
    student_id: students[0]?.id || "",
    arrival_enabled: true,
    departure_enabled: true,
    late_enabled: true,
    absence_enabled: true,
    class_end_enabled: true
  });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setMsg("");
    setLoading(true);
    try {
      await api.post("/api/notifications/settings", { ...form, student_id: parseInt(form.student_id) });
      setMsg("Settings saved successfully!");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update notification settings. (Note: Only linked parents can configure this)");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title="Configure Notification Alerts" onClose={onClose}>
      <form onSubmit={submit} className="modal-form">
        <label>
          Select Student *
          <select value={form.student_id} onChange={(e) => set("student_id", e.target.value)} required>
            <option value="">Select student</option>
            {students.map((s) => (
              <option key={s.id} value={s.id}>
                {[s.first_name, s.middle_name, s.last_name].filter(Boolean).join(" ")} ({s.student_code})
              </option>
            ))}
          </select>
        </label>
        <div style={{ display: "grid", gap: 12, marginTop: 16 }}>
          {[
            { key: "arrival_enabled", label: "🟢 Arrival Alert (Student checks in)" },
            { key: "departure_enabled", label: "🔴 Departure Alert (Student leaves school)" },
            { key: "late_enabled", label: "⚠️ Late Alert (Arrived past start time)" },
            { key: "absence_enabled", label: "❌ Absence Alert (Unexcused missing student)" },
            { key: "class_end_enabled", label: "🔔 End of School Day Alert" }
          ].map((item) => (
            <label key={item.key} style={{ display: "flex", alignItems: "center", gap: 10, margin: 0 }}>
              <input
                type="checkbox"
                style={{ width: "auto", margin: 0 }}
                checked={form[item.key]}
                onChange={(e) => set(item.key, e.target.checked)}
              />
              <span>{item.label}</span>
            </label>
          ))}
        </div>
        {msg && <div className="modal-success" style={{ marginTop: 16 }}>{msg}</div>}
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading || !form.student_id}>{loading ? "Saving" : "Save Preferences"}</button>
      </form>
    </Modal>
  );
}

/* 
   PAGES
    */

/*  Dashboard Page  */
function DashboardView({ onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.get("/api/dashboard/")
      .then((r) => setData(r.data))
      .catch(() => { })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);
  const d = data || { total_students: 0, present: 0, late: 0, absent: 0, classes: 0, date: "" };

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SYSTEM OVERVIEW</div>
          <h2>Good day </h2>
          <p>Live school status & attendance dashboard  {d.date || "Today"}</p>
        </div>
        <div className="header-actions">
          <button className="secondary" onClick={load}><RefreshCw size={15} /> Refresh</button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon"><Users size={22} /></div>
          <div>
            <div className="stat-title">Total Active Students</div>
            <div className="stat-value">{d.total_students}</div>
            <div className="stat-note">Enrolled across all classes</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon success"><CheckCircle2 size={22} /></div>
          <div>
            <div className="stat-title">Present Today</div>
            <div className="stat-value">{d.present}</div>
            <div className="stat-note">Safely checked in</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon warning"><Clock3 size={22} /></div>
          <div>
            <div className="stat-title">Late Arrivals</div>
            <div className="stat-value">{d.late}</div>
            <div className="stat-note">Checked in after start time</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon danger"><X size={22} /></div>
          <div>
            <div className="stat-title">Absent</div>
            <div className="stat-value">{d.absent}</div>
            <div className="stat-note">No arrival record</div>
          </div>
        </div>
      </div>

      <div className="panel-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <h3>Overall Attendance Health</h3>
              <p>Percentage of students present today</p>
            </div>
            <span className="pill success">Live Sync</span>
          </div>
          <div className="progress-wrap">
            <div className="progress">
              <span style={{ width: `${d.total_students ? Math.round((d.present / d.total_students) * 100) : 0}%` }} />
            </div>
            <strong>{d.total_students ? Math.round((d.present / d.total_students) * 100) : 0}%</strong>
          </div>
          <div className="legend">
            <span><i className="dot present" /> Present ({d.present})</span>
            <span><i className="dot late" /> Late ({d.late})</span>
            <span><i className="dot absent" /> Absent ({d.absent})</span>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <h3>Telegram Notification Bridge</h3>
              <p>Real-time instant bot alerts</p>
            </div>
            <Send size={18} color="#0284c7" />
          </div>
          <div className="alert-card">
            <div className="telegram-badge"></div>
            <div>
              <strong>Automated Parent Dispatch Active</strong>
              <p>Arrival & departure records trigger instantaneous notifications to linked Telegram chat IDs.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/*  Schools Page  */
function SchoolsView() {
  const [schools, setSchools] = useState([]);
  const [modal, setModal] = useState(false);
  const [editSchool, setEditSchool] = useState(null);
  const [deleteSchool, setDeleteSchool] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [search, setSearch] = useState("");

  const load = (msg) => {
    api.get("/api/schools/").then((r) => setSchools(r.data)).catch(() => { });
    if (msg) setFeedback({ type: "success", message: msg });
  };
  useEffect(() => { load(); }, []);

  const handleDelete = async () => {
    if (!deleteSchool) return;
    const name = deleteSchool.name;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/schools/${deleteSchool.id}`);
      setDeleteSchool(null);
      load(`School "${name}" deleted successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to delete school" });
      setDeleteSchool(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const filtered = schools.filter((s) =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {modal && <AddSchoolModal onClose={() => setModal(false)} onSaved={() => load("School created successfully")} />}
      {editSchool && <EditSchoolModal key={editSchool.id} school={editSchool} onClose={() => setEditSchool(null)} onSaved={(msg) => load(msg || "School updated successfully")} />}
      {deleteSchool && (
        <ConfirmModal
          title="Delete School"
          message={`Are you sure you want to permanently delete "${deleteSchool.name}" (${deleteSchool.code})?`}
          onConfirm={handleDelete}
          onClose={() => setDeleteSchool(null)}
          loading={deleteLoading}
        />
      )}

      <div className="page-heading">
        <div>
          <div className="eyebrow">INSTITUTION STRUCTURE</div>
          <h2>Registered Schools</h2>
          <p>Manage schools, campus codes and contact details.</p>
        </div>
        <button className="primary" onClick={() => setModal(true)}><Plus size={16} /> Add School</button>
      </div>

      <AlertBanner feedback={feedback} onClose={() => setFeedback(null)} />

      <div className="panel table-panel">
        <div className="table-toolbar">
          <div className="searchbox">
            <Search size={16} />
            <input placeholder="Filter schools..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <span className="pill info">{filtered.length} Schools</span>
        </div>
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Address</th>
                <th>Phone</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr key={s.id}>
                  <td><strong>{s.code}</strong></td>
                  <td>{s.name}</td>
                  <td>{s.address || ""}</td>
                  <td>{s.phone || ""}</td>
                  <td><span className="status present">{s.status || "ACTIVE"}</span></td>
                  <td>
                    <div className="action-btns">
                      <button className="btn-sm-edit" onClick={() => setEditSchool(s)}>
                        <Pencil size={13} /> Edit
                      </button>
                      <button className="btn-sm-danger" onClick={() => { setFeedback(null); setDeleteSchool(s); }}>
                        <Trash2 size={13} /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!filtered.length && <div className="empty">No schools registered yet. Click "+ Add School" to create one.</div>}
        </div>
      </div>
    </div>
  );
}

/*  Classes Page  */
function ClassesView() {
  const [classes, setClasses] = useState([]);
  const [schools, setSchools] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [modalClass, setModalClass] = useState(false);
  const [modalAssign, setModalAssign] = useState(false);
  const [modalTeacher, setModalTeacher] = useState(false);
  const [editClass, setEditClass] = useState(null);
  const [deleteClass, setDeleteClass] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [search, setSearch] = useState("");

  const load = (msg) => {
    api.get("/api/classes/").then((r) => setClasses(r.data)).catch(() => { });
    api.get("/api/schools/").then((r) => setSchools(r.data)).catch(() => { });
    api.get("/api/users/").then((r) => setTeachers(r.data.filter((u) => u.role === "TEACHER"))).catch(() => { });
    if (msg) setFeedback({ type: "success", message: msg });
  };
  useEffect(() => { load(); }, []);

  const handleDelete = async () => {
    if (!deleteClass) return;
    const name = deleteClass.class_name;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/classes/${deleteClass.id}`);
      setDeleteClass(null);
      load(`Class "${name}" deleted successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to delete class" });
      setDeleteClass(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const filtered = classes.filter((c) =>
    c.class_name.toLowerCase().includes(search.toLowerCase()) ||
    c.class_code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {modalClass && <AddClassModal schools={schools} onClose={() => setModalClass(false)} onSaved={() => load("Class created successfully")} />}
      {modalTeacher && <AddTeacherModal classes={classes} onClose={() => setModalTeacher(false)} onSaved={() => load("Teacher account created successfully")} />}
      {modalAssign && (
        <AssignTeacherModal
          classes={classes}
          teachers={teachers}
          onClose={() => setModalAssign(false)}
          onSaved={() => load("Teacher assigned to class successfully")}
          onOpenAddTeacher={() => { setModalAssign(false); setModalTeacher(true); }}
        />
      )}
      {editClass && (
        <EditClassModal key={editClass.id} cls={editClass} schools={schools} onClose={() => setEditClass(null)} onSaved={(msg) => load(msg || "Class updated successfully")} />
      )}
      {deleteClass && (
        <ConfirmModal
          title="Delete Class"
          message={`Are you sure you want to delete class "${deleteClass.class_name}" (${deleteClass.class_code})? Any assigned students will become unassigned.`}
          onConfirm={handleDelete}
          onClose={() => setDeleteClass(null)}
          loading={deleteLoading}
        />
      )}

      <div className="page-heading">
        <div>
          <div className="eyebrow">ACADEMIC ROOMS</div>
          <h2>Classes & Sections</h2>
          <p>Configure classes, daily bell schedules, and assign teachers.</p>
        </div>
        <div className="header-actions">
          <button className="secondary" onClick={() => setModalTeacher(true)}><UserPlus size={16} /> Add Teacher</button>
          <button className="secondary" onClick={() => setModalAssign(true)}><Link2 size={16} /> Assign Teacher</button>
          <button className="primary" onClick={() => setModalClass(true)}><Plus size={16} /> Add Class</button>
        </div>
      </div>

      <AlertBanner feedback={feedback} onClose={() => setFeedback(null)} />

      <div className="panel table-panel">
        <div className="table-toolbar">
          <div className="searchbox">
            <Search size={16} />
            <input placeholder="Filter classes..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <span className="pill info">{filtered.length} Classes</span>
        </div>
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Grade</th>
                <th>Section</th>
                <th>Academic Year</th>
                <th>Schedule</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id}>
                  <td><strong>{c.class_code}</strong></td>
                  <td>{c.class_name}</td>
                  <td>{c.grade}</td>
                  <td>{c.section || ""}</td>
                  <td>{c.academic_year}</td>
                  <td>{c.school_start_time ? `${c.school_start_time.slice(0, 5)} - ${c.school_end_time?.slice(0, 5)}` : "Default"}</td>
                  <td><span className="status present">{c.status || "ACTIVE"}</span></td>
                  <td>
                    <div className="action-btns">
                      <button className="btn-sm-edit" onClick={() => setEditClass(c)}>
                        <Pencil size={13} /> Edit
                      </button>
                      <button className="btn-sm-danger" onClick={() => { setFeedback(null); setDeleteClass(c); }}>
                        <Trash2 size={13} /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!filtered.length && <div className="empty">No classes configured. Click "+ Add Class" to set up classroom structures.</div>}
        </div>
      </div>
    </div>
  );
}

/*  Teachers Page  */
function TeachersView() {
  const [teachers, setTeachers] = useState([]);
  const [classes, setClasses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [modalAddTeacher, setModalAddTeacher] = useState(false);
  const [modalAssign, setModalAssign] = useState(false);
  const [selectedTeacherForAssign, setSelectedTeacherForAssign] = useState(null);
  const [editTeacher, setEditTeacher] = useState(null);
  const [deleteTeacher, setDeleteTeacher] = useState(null);
  const [unassignTarget, setUnassignTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const load = (msg) => {
    setLoading(true);
    Promise.all([
      api.get("/api/users/").then((r) => setTeachers(r.data.filter((u) => u.role === "TEACHER"))).catch(() => []),
      api.get("/api/classes/").then((r) => setClasses(r.data)).catch(() => []),
      api.get("/api/classes/teacher-assignments").then((r) => setAssignments(r.data)).catch(() => []),
    ]).finally(() => setLoading(false));
    if (msg) setFeedback({ type: "success", message: msg });
  };

  useEffect(() => { load(); }, []);

  const handleDeleteTeacher = async () => {
    if (!deleteTeacher) return;
    const name = deleteTeacher.full_name;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/users/${deleteTeacher.id}`);
      setDeleteTeacher(null);
      load(`Teacher "${name}" deleted successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to delete teacher" });
      setDeleteTeacher(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleUnassign = async () => {
    if (!unassignTarget) return;
    const { teacherName, className } = unassignTarget;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/classes/teacher-assignments/${unassignTarget.id}`);
      setUnassignTarget(null);
      load(`Teacher "${teacherName}" unassigned from "${className}" successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to unassign class" });
      setUnassignTarget(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const teacherClassesMap = {};
  assignments.forEach((a) => {
    if (!teacherClassesMap[a.teacher_id]) teacherClassesMap[a.teacher_id] = [];
    teacherClassesMap[a.teacher_id].push(a);
  });

  const filtered = teachers.filter((t) => {
    const q = search.toLowerCase();
    const nameMatch = t.full_name.toLowerCase().includes(q);
    const emailMatch = (t.email || "").toLowerCase().includes(q);
    const phoneMatch = (t.phone || "").toLowerCase().includes(q);
    const classesList = teacherClassesMap[t.id] || [];
    const classMatch = classesList.some((c) => c.class_name.toLowerCase().includes(q) || c.class_code.toLowerCase().includes(q));
    return nameMatch || emailMatch || phoneMatch || classMatch;
  });

  return (
    <div>
      {modalAddTeacher && (
        <AddTeacherModal classes={classes} onClose={() => setModalAddTeacher(false)} onSaved={() => load("Teacher account created successfully")} />
      )}
      {modalAssign && (
        <AssignTeacherModal
          classes={classes}
          teachers={teachers}
          initialTeacherId={selectedTeacherForAssign}
          onClose={() => { setModalAssign(false); setSelectedTeacherForAssign(null); }}
          onSaved={() => load("Teacher assigned to class successfully")}
          onOpenAddTeacher={() => { setModalAssign(false); setModalAddTeacher(true); }}
        />
      )}
      {editTeacher && (
        <EditUserModal key={editTeacher.id} user={editTeacher} onClose={() => setEditTeacher(null)} onSaved={(msg) => load(msg || "Teacher profile updated successfully")} />
      )}
      {deleteTeacher && (
        <ConfirmModal
          title="Delete Teacher"
          message={`Are you sure you want to delete teacher "${deleteTeacher.full_name}"? Their class assignments and system profile will be removed.`}
          onConfirm={handleDeleteTeacher}
          onClose={() => setDeleteTeacher(null)}
          loading={deleteLoading}
        />
      )}
      {unassignTarget && (
        <ConfirmModal
          title="Unassign Class"
          message={`Unassign ${unassignTarget.teacherName} from "${unassignTarget.className}"?`}
          onConfirm={handleUnassign}
          onClose={() => setUnassignTarget(null)}
          loading={deleteLoading}
        />
      )}

      <div className="page-heading">
        <div>
          <div className="eyebrow">ACADEMIC FACULTY</div>
          <h2>Teachers Directory</h2>
          <p>Register teaching staff, contact information, and classroom assignments.</p>
        </div>
        <div className="header-actions">
          <button className="secondary" onClick={() => { setSelectedTeacherForAssign(null); setModalAssign(true); }}>
            <Link2 size={16} /> Assign to Class
          </button>
          <button className="primary" onClick={() => setModalAddTeacher(true)}>
            <UserPlus size={16} /> Add Teacher
          </button>
        </div>
      </div>

      <AlertBanner feedback={feedback} onClose={() => setFeedback(null)} />

      <div className="panel table-panel">
        <div className="table-toolbar">
          <div className="searchbox">
            <Search size={16} />
            <input
              placeholder="Search teachers by name, email, or class..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <span className="pill info">{filtered.length} Teachers</span>
        </div>
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Teacher</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Assigned Classes</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => {
                const assigned = teacherClassesMap[t.id] || [];
                return (
                  <tr key={t.id}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{
                          width: 34, height: 34, borderRadius: "50%",
                          background: "#eef2ff", color: "#4f46e5",
                          fontWeight: 700, fontSize: 13,
                          display: "flex", alignItems: "center", justifyContent: "center"
                        }}>
                          {t.full_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <strong>{t.full_name}</strong>
                          {t.telegram_id && (
                            <div style={{ fontSize: 11, color: "#0284c7" }}>Telegram linked</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>{t.email || "—"}</td>
                    <td>{t.phone || "—"}</td>
                    <td>
                      {assigned.length > 0 ? (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                          {assigned.map((c) => (
                            <span
                              key={c.id}
                              style={{
                                background: "#f0fdf4", color: "#166534",
                                border: "1px solid #bbf7d0", borderRadius: 6,
                                padding: "2px 8px", fontSize: 12, fontWeight: 600,
                                display: "inline-flex", alignItems: "center", gap: 4
                              }}
                            >
                              {c.class_name} ({c.class_code})
                              <button
                                className="chip-remove"
                                title="Unassign class"
                                onClick={() => setUnassignTarget({ id: c.id, teacherName: t.full_name, className: c.class_name })}
                              >
                                ✕
                              </button>
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span style={{ fontSize: 12, color: "var(--muted)" }}>No classes assigned</span>
                      )}
                    </td>
                    <td><span className="status present">{t.status || "ACTIVE"}</span></td>
                    <td>
                      <div className="action-btns">
                        <button
                          className="secondary btn-sm"
                          onClick={() => { setSelectedTeacherForAssign(t.id); setModalAssign(true); }}
                        >
                          <Link2 size={13} /> Assign
                        </button>
                        <button className="btn-sm-edit" onClick={() => setEditTeacher(t)}>
                          <Pencil size={13} /> Edit
                        </button>
                        <button className="btn-sm-danger" onClick={() => { setFeedback(null); setDeleteTeacher(t); }}>
                          <Trash2 size={13} /> Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!loading && !filtered.length && (
            <div className="empty">
              No teachers registered yet. Click "+ Add Teacher" to add your first faculty member.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/*  Students Page  */
function StudentsView() {
  const [students, setStudents] = useState([]);
  const [schools, setSchools] = useState([]);
  const [classes, setClasses] = useState([]);
  const [modalAdd, setModalAdd] = useState(false);
  const [editStudent, setEditStudent] = useState(null);
  const [deleteStudent, setDeleteStudent] = useState(null);
  const [selectedStudentId, setSelectedStudentId] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [search, setSearch] = useState("");

  const load = (msg) => {
    api.get("/api/students/").then((r) => setStudents(r.data)).catch(() => { });
    api.get("/api/schools/").then((r) => setSchools(r.data)).catch(() => { });
    api.get("/api/classes/").then((r) => setClasses(r.data)).catch(() => { });
    if (msg) setFeedback({ type: "success", message: msg });
  };
  useEffect(() => { load(); }, []);

  const handleDeleteStudent = async () => {
    if (!deleteStudent) return;
    const name = `${deleteStudent.first_name} ${deleteStudent.last_name || ""}`.trim();
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/students/${deleteStudent.id}`);
      setDeleteStudent(null);
      load(`Student "${name}" deleted successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to delete student" });
      setDeleteStudent(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const filtered = students.filter((s) => {
    const fullName = `${s.first_name} ${s.middle_name || ""} ${s.last_name || ""}`.toLowerCase();
    return fullName.includes(search.toLowerCase()) || s.student_code.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div>
      {modalAdd && <AddStudentModal schools={schools} classes={classes} onClose={() => setModalAdd(false)} onSaved={() => load("Student enrolled successfully")} />}
      {editStudent && (
        <EditStudentModal
          key={editStudent.id}
          student={editStudent}
          schools={schools}
          classes={classes}
          onClose={() => setEditStudent(null)}
          onSaved={(msg) => load(msg || "Student profile updated successfully")}
        />
      )}
      {deleteStudent && (
        <ConfirmModal
          title="Delete Student"
          message={`Are you sure you want to permanently delete student "${deleteStudent.first_name} ${deleteStudent.last_name || ""}" (${deleteStudent.student_code})? All attendance records and parent links will also be removed.`}
          onConfirm={handleDeleteStudent}
          onClose={() => setDeleteStudent(null)}
          loading={deleteLoading}
        />
      )}
      {selectedStudentId && <StudentDetailsModal studentId={selectedStudentId} onClose={() => setSelectedStudentId(null)} />}

      <div className="page-heading">
        <div>
          <div className="eyebrow">STUDENT DIRECTORY</div>
          <h2>Enrolled Students</h2>
          <p>Roster of all enrolled students, security QR codes and attendance trails.</p>
        </div>
        <button className="primary" onClick={() => setModalAdd(true)}><Plus size={16} /> Add Student</button>
      </div>

      <AlertBanner feedback={feedback} onClose={() => setFeedback(null)} />

      <div className="panel table-panel">
        <div className="table-toolbar">
          <div className="searchbox">
            <Search size={16} />
            <input placeholder="Search student code or name..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <span className="pill info">{filtered.length} Students</span>
        </div>
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Full Name</th>
                <th>Gender</th>
                <th>Class</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => {
                const cls = classes.find((c) => c.id === s.class_id);
                return (
                  <tr key={s.id}>
                    <td><strong>{s.student_code}</strong></td>
                    <td>{[s.first_name, s.middle_name, s.last_name].filter(Boolean).join(" ")}</td>
                    <td>{s.gender || ""}</td>
                    <td>{cls ? cls.class_name : (s.class_id ? `Class #${s.class_id}` : "Unassigned")}</td>
                    <td><span className="status present">{s.status}</span></td>
                    <td>
                      <div className="action-btns">
                        <button className="secondary btn-sm" onClick={() => setSelectedStudentId(s.id)}>
                          <Eye size={13} /> Logs
                        </button>
                        <button className="btn-sm-edit" onClick={() => setEditStudent(s)}>
                          <Pencil size={13} /> Edit
                        </button>
                        <button className="btn-sm-danger" onClick={() => { setFeedback(null); setDeleteStudent(s); }}>
                          <Trash2 size={13} /> Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!filtered.length && <div className="empty">No students found.</div>}
        </div>
      </div>
    </div>
  );
}

/*  Attendance Page (Bulk)  */
function AttendanceView() {
  const today = new Date().toISOString().split("T")[0];
  const [selectedDate, setSelectedDate] = useState(today);
  const [eventType, setEventType] = useState("ARRIVAL"); // "ARRIVAL" | "DEPARTURE" | "STATUS"
  const [students, setStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [existingRecords, setExistingRecords] = useState([]);
  const [checked, setChecked] = useState(new Set());
  const [studentStatuses, setStudentStatuses] = useState({});  // id -> status string
  const [filterClass, setFilterClass] = useState("");
  const [search, setSearch] = useState("");
  const [method, setMethod] = useState("TEACHER");
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState(null);
  const [departurePendingOnly, setDeparturePendingOnly] = useState(false);
  const [editAttendance, setEditAttendance] = useState(null);
  const [deleteAttendance, setDeleteAttendance] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleDeleteAttendance = async () => {
    if (!deleteAttendance) return;
    const sName = deleteAttendance.studentName;
    setDeleteLoading(true);
    setSaveResult(null);
    try {
      await api.delete(`/api/attendance/${deleteAttendance.id}`);
      setDeleteAttendance(null);
      loadAttendance();
      setSaveResult({ success: true, message: `Attendance record for "${sName}" deleted successfully.` });
    } catch (err) {
      setSaveResult({ success: false, message: err.response?.data?.detail || "Failed to delete attendance record" });
      setDeleteAttendance(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/api/students/").then((r) => setStudents(r.data)).catch(() => { });
    api.get("/api/classes/").then((r) => setClasses(r.data)).catch(() => { });
  }, []);

  const loadAttendance = () => {
    setLoading(true);
    setChecked(new Set());
    setStudentStatuses({});
    const endpoint = selectedDate === today
      ? "/api/attendance/today"
      : `/api/attendance/date/${selectedDate}`;
    api.get(endpoint)
      .then((r) => setExistingRecords(r.data))
      .catch(() => setExistingRecords([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadAttendance(); }, [selectedDate]);
  useEffect(() => { setChecked(new Set()); setStudentStatuses({}); setSaveResult(null); }, [eventType]);

  const recordMap = {};
  existingRecords.forEach((r) => { recordMap[r.student_id] = r; });
  const classMap = {};
  classes.forEach((c) => { classMap[c.id] = c.class_name; });

  const isStudentPresentToday = (studentId) => {
    const rec = recordMap[studentId];
    if (!rec) return false;
    return (
      rec.status === "PRESENT" ||
      rec.status === "LATE" ||
      (Boolean(rec.arrival_time) && rec.status !== "ABSENT" && rec.status !== "EXCUSED")
    );
  };

  const visibleStudents = students.filter((s) => {
    const name = `${s.first_name} ${s.middle_name || ""} ${s.last_name || ""}`.toLowerCase();
    const matchSearch = name.includes(search.toLowerCase()) || s.student_code.toLowerCase().includes(search.toLowerCase());
    const matchClass = !filterClass || String(s.class_id) === filterClass;
    if (!matchSearch || !matchClass) return false;
    if (eventType === "DEPARTURE") {
      if (!isStudentPresentToday(s.id)) return false;
      if (departurePendingOnly && recordMap[s.id]?.departure_time) return false;
      return true;
    }
    return true;
  });

  const toggle = (id) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
    setStudentStatuses((prev) => prev[id] ? prev : { ...prev, [id]: "PRESENT" });
  };

  const setStatus = (id, status) => setStudentStatuses((prev) => ({ ...prev, [id]: status }));

  const selectAll = () => {
    if (eventType === "DEPARTURE") {
      const notDeparted = visibleStudents.filter((s) => !recordMap[s.id]?.departure_time);
      const targets = notDeparted.length > 0 ? notDeparted : visibleStudents;
      setChecked(new Set(targets.map((s) => s.id)));
    } else {
      setChecked(new Set(visibleStudents.map((s) => s.id)));
    }
    setStudentStatuses((prev) => {
      const next = { ...prev };
      visibleStudents.forEach((s) => { if (!next[s.id]) next[s.id] = "PRESENT"; });
      return next;
    });
  };
  const clearAll = () => { setChecked(new Set()); setStudentStatuses({}); };
  const checkedCount = checked.size;

  const handleSave = async () => {
    if (!checkedCount) return;
    setSaving(true);
    setSaveResult(null);
    try {
      let saved = 0;
      if (eventType === "STATUS") {
        const groups = {};
        [...checked].forEach((id) => {
          const st = studentStatuses[id] || "PRESENT";
          if (!groups[st]) groups[st] = [];
          groups[st].push(id);
        });
        const promises = Object.entries(groups).map(([status, ids]) =>
          api.post("/api/attendance/bulk", {
            student_ids: ids,
            attendance_date: selectedDate,
            event_type: "STATUS",
            status,
            method,
          })
        );
        const responses = await Promise.all(promises);
        saved = responses.reduce((acc, r) => acc + (r.data?.length || 0), 0);
        setSaveResult({ success: true, message: `⚡ Saved roll call for ${saved} student(s) instantly! Parent alerts dispatched.` });
      } else {
        const res = await api.post("/api/attendance/bulk", {
          student_ids: [...checked],
          attendance_date: selectedDate,
          event_type: eventType,
          method,
        });
        saved = res.data?.length || 0;
        const label = eventType === "ARRIVAL" ? "Arrivals" : "Departures";
        setSaveResult({ success: true, message: `⚡ Saved ${saved} ${label} for ${selectedDate} instantly! Parent alerts dispatched.` });
      }
      loadAttendance();
    } catch (err) {
      setSaveResult({ success: false, message: `❌ Failed: ${err.response?.data?.detail || err.message}` });
    } finally {
      setSaving(false);
    }
  };

  const fmtTime = (dt) => dt ? new Date(dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";

  const isArrival = eventType === "ARRIVAL";
  const isDeparture = eventType === "DEPARTURE";
  const isStatus = eventType === "STATUS";
  const modeColor = isArrival ? "#10b981" : isDeparture ? "#f59e0b" : "#6366f1";
  const modeIcon = isArrival ? "🟢" : isDeparture ? "🔴" : "📋";
  const modeLabel = isArrival ? "Arrival Check-In" : isDeparture ? "Departure Check-Out" : "Roll Call";

  const MODE_BTN = (key, icon, label, activeColor, activeBg, activeText) => (
    <button
      type="button"
      onClick={() => setEventType(key)}
      className="att-mode-btn"
      style={{
        borderColor: eventType === key ? activeColor : "#e2e8f0",
        background: eventType === key ? activeBg : "#f8fafc",
        color: eventType === key ? activeText : "#64748b",
      }}
    >
      <span>{icon}</span> <span>{label}</span>
    </button>
  );

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">DAILY GATE LOGS</div>
          <h2>Bulk Attendance Register</h2>
          <p>Register arrivals, departures, and roll-call status. Parents receive instant Telegram notifications.</p>
        </div>
      </div>

      {/* Controls Panel */}
      <div className="panel" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 14, alignItems: "flex-start" }}>

          {/* Mode Toggle */}
          <div style={{ flex: "1 1 100%", width: "100%" }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", marginBottom: 8 }}>
              ⚙️ Registration Mode
            </div>
            <div className="att-mode-group">
              {MODE_BTN("ARRIVAL", "🟢", "Arrival (Morning)", "#10b981", "#ecfdf5", "#065f46")}
              {MODE_BTN("DEPARTURE", "🔴", "Departure (End of Day)", "#f59e0b", "#fffbeb", "#92400e")}
              {MODE_BTN("STATUS", "📋", "Roll Call (Status)", "#6366f1", "#eef2ff", "#3730a3")}
            </div>
            {isDeparture && (
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginTop: 8 }}>
                <p style={{ fontSize: 12, color: "#92400e", margin: 0, background: "#fffbeb", padding: "6px 12px", borderRadius: 8, border: "1px solid #fde68a" }}>
                  Showing only present students for departure checkout.
                </p>
                {students.some((s) => isStudentPresentToday(s.id) && recordMap[s.id]?.departure_time) && (
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#92400e", fontWeight: 600, cursor: "pointer", background: "#fffbeb", padding: "6px 10px", borderRadius: 8, border: "1px solid #fde68a" }}>
                    <input
                      type="checkbox"
                      style={{ width: "auto", margin: 0, cursor: "pointer" }}
                      checked={departurePendingOnly}
                      onChange={(e) => setDeparturePendingOnly(e.target.checked)}
                    />
                    Hide already departed
                  </label>
                )}
              </div>
            )}
            {isStatus && (
              <p style={{ fontSize: 12, color: "#3730a3", marginTop: 8, background: "#eef2ff", padding: "6px 12px", borderRadius: 8, border: "1px solid #c7d2fe" }}>
                Select students and choose their status (Present / Absent / Late / Excused). On mobile, tap any status pill directly!
              </p>
            )}
          </div>

          {/* Date */}
          <label style={{ flex: "1 1 140px", minWidth: 0 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", display: "block", marginBottom: 6 }}>📅 Date</span>
            <input type="date" value={selectedDate} max={today}
              onChange={(e) => { setSelectedDate(e.target.value); setSaveResult(null); }}
              style={{ width: "100%", minWidth: 0 }} />
          </label>

          {/* Class */}
          <label style={{ flex: "1 1 160px", minWidth: 0 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", display: "block", marginBottom: 6 }}>🏫 Class</span>
            <select value={filterClass} onChange={(e) => setFilterClass(e.target.value)} style={{ width: "100%", minWidth: 0 }}>
              <option value="">All Classes</option>
              {classes.map((c) => <option key={c.id} value={String(c.id)}>{c.class_name} ({c.class_code})</option>)}
            </select>
          </label>

          {/* Search */}
          <label style={{ flex: "2 1 180px", minWidth: 0 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", display: "block", marginBottom: 6 }}>🔍 Search</span>
            <div className="searchbox" style={{ margin: 0, width: "100%" }}>
              <Search size={15} />
              <input placeholder="Name or code" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </label>

          {/* Method */}
          <label style={{ flex: "1 1 140px", minWidth: 0 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", display: "block", marginBottom: 6 }}>📋 Method</span>
            <select value={method} onChange={(e) => setMethod(e.target.value)} style={{ width: "100%", minWidth: 0 }}>
              <option value="TEACHER">Teacher Check</option>
              <option value="SECURITY">Security Gate</option>
              <option value="RFID">RFID Card</option>
              <option value="BIOMETRIC">Biometric</option>
            </select>
          </label>
        </div>
      </div>

      <AlertBanner
        feedback={saveResult ? { type: saveResult.success ? "success" : "error", message: saveResult.message } : null}
        onClose={() => setSaveResult(null)}
      />

      {/* Student Checklist */}
      <div className="panel table-panel" style={{ marginBottom: 24 }}>
        <div className="table-toolbar att-toolbar">
          <div className="att-toolbar-header">
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <span style={{
                background: isArrival ? "#ecfdf5" : isDeparture ? "#fffbeb" : "#eef2ff",
                color: isArrival ? "#065f46" : isDeparture ? "#92400e" : "#3730a3",
                border: `1px solid ${isArrival ? "#6ee7b7" : isDeparture ? "#fde68a" : "#c7d2fe"}`,
                borderRadius: 20, padding: "4px 12px", fontSize: 12, fontWeight: 700
              }}>
                {modeIcon} {modeLabel}
              </span>
              <span className="pill info">{visibleStudents.length} Students</span>
              <span className="pill success">{checkedCount} Selected</span>
            </div>
          </div>
          <div className="att-toolbar-actions">
            <div className="att-toolbar-btn-row">
              <button className="secondary btn-sm" onClick={selectAll}>Select All</button>
              <button className="secondary btn-sm" onClick={clearAll}>Clear</button>
            </div>
            <button className="primary att-save-btn-mobile" onClick={handleSave}
              disabled={saving || checkedCount === 0}
              style={{ background: saving ? undefined : modeColor }}>
              {saving ? "Saving & Notifying..." : `${modeIcon} Save (${checkedCount}) & Notify Parents`}
            </button>
          </div>
        </div>

        {/* 1. Desktop Table View (visible on desktop/tablet) */}
        <div className="attendance-desktop-table table-responsive">
          <table>
            <thead>
              <tr>
                <th style={{ width: 44, textAlign: "center" }}></th>
                <th>Student</th>
                <th>Code</th>
                <th>Class</th>
                <th>Arrived At</th>
                {isStatus ? <th>Status to Set</th> : <th>{isArrival ? "Today's Status" : "Departed At"}</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: "center", padding: 32, color: "var(--muted)" }}>Loading...</td></tr>
              ) : visibleStudents.map((s) => {
                const isChecked = checked.has(s.id);
                const rec = recordMap[s.id];
                const currentStatus = studentStatuses[s.id] || "PRESENT";
                const sName = [s.first_name, s.middle_name, s.last_name].filter(Boolean).join(" ");
                return (
                  <tr key={s.id} className={isChecked ? "row-selected" : ""}
                    onClick={() => toggle(s.id)} style={{ cursor: "pointer" }}>
                    <td style={{ textAlign: "center" }} onClick={(e) => e.stopPropagation()}>
                      <input type="checkbox" checked={isChecked} onChange={() => toggle(s.id)}
                        style={{ margin: 0, cursor: "pointer", width: 18, height: 18 }} />
                    </td>
                    <td><strong>{sName}</strong></td>
                    <td><code style={{ fontSize: 12 }}>{s.student_code}</code></td>
                    <td>{classMap[s.class_id] || ""}</td>
                    <td style={{ fontSize: 13 }}>
                      {rec?.arrival_time
                        ? <span style={{ color: "#059669", fontWeight: 600 }}> {fmtTime(rec.arrival_time)}</span>
                        : rec?.status === "PRESENT" || rec?.status === "LATE"
                          ? <span style={{ color: "#059669", fontWeight: 500 }}>Present (Roll Call)</span>
                          : <span style={{ color: "var(--muted)" }}>Not recorded</span>}
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      {isStatus && isChecked ? (
                        <select
                          value={currentStatus}
                          onChange={(e) => setStatus(s.id, e.target.value)}
                          style={{
                            fontSize: 13, padding: "5px 10px", borderRadius: 8, minWidth: 150,
                            fontWeight: 600, cursor: "pointer",
                            borderColor: currentStatus === "PRESENT" ? "#10b981"
                              : currentStatus === "LATE" ? "#f59e0b"
                                : currentStatus === "ABSENT" ? "#ef4444" : "#8b5cf6",
                          }}
                        >
                          <option value="PRESENT">Present</option>
                          <option value="LATE">Late</option>
                          <option value="ABSENT">Absent</option>
                          <option value="EXCUSED">Excused</option>
                        </select>
                      ) : isStatus && !isChecked ? (
                        <span style={{ fontSize: 12, color: "var(--muted)" }}>select to set</span>
                      ) : isDeparture ? (
                        rec?.departure_time
                          ? <span style={{ color: "#d97706", fontWeight: 600 }}> {fmtTime(rec.departure_time)}</span>
                          : <span style={{ color: "var(--muted)" }}>Not departed</span>
                      ) : (
                        rec ? <span className={`status ${rec.status?.toLowerCase()}`}>{rec.status}</span>
                          : <span style={{ fontSize: 12, color: "var(--muted)" }}>No record</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!loading && !visibleStudents.length && (
            <div className="empty">
              {isDeparture
                ? "No present students found for this date. Register morning arrivals or mark students present in Roll Call first."
                : "No students match your filters."}
            </div>
          )}
        </div>

        {/* 2. Mobile Card List (visible on phones) */}
        <div className="attendance-mobile-cards">
          {loading ? (
            <div style={{ textAlign: "center", padding: 32, color: "var(--muted)" }}>Loading students...</div>
          ) : !visibleStudents.length ? (
            <div className="empty">
              {isDeparture
                ? "No present students found for this date. Register morning arrivals or mark students present in Roll Call first."
                : "No students match your filters."}
            </div>
          ) : (
            visibleStudents.map((s) => {
              const isChecked = checked.has(s.id);
              const rec = recordMap[s.id];
              const currentStatus = studentStatuses[s.id] || "PRESENT";
              const sFullName = [s.first_name, s.middle_name, s.last_name].filter(Boolean).join(" ");
              return (
                <div
                  key={s.id}
                  className={`att-mobile-card ${isChecked ? "att-card-selected" : ""}`}
                  onClick={() => toggle(s.id)}
                >
                  <div className="att-card-header">
                    <div className="att-card-check-wrap" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggle(s.id)}
                        className="att-card-checkbox"
                      />
                    </div>
                    <div className="att-card-info">
                      <div className="att-card-name">{sFullName}</div>
                      <div className="att-card-meta">
                        <span className="code-chip">{s.student_code}</span>
                        {classMap[s.class_id] && <span className="class-chip">{classMap[s.class_id]}</span>}
                      </div>
                    </div>
                    <div className="att-card-quick-status">
                      {rec?.arrival_time ? (
                        <span className="badge-arrival">🕒 {fmtTime(rec.arrival_time)}</span>
                      ) : rec?.status ? (
                        <span className={`status ${rec.status.toLowerCase()}`}>{rec.status}</span>
                      ) : (
                        <span className="badge-unrecorded">Not marked</span>
                      )}
                    </div>
                  </div>

                  {/* If in Roll Call (STATUS) mode: show prominent, touch-friendly status buttons right on the card! */}
                  {isStatus && (
                    <div className="att-card-status-bar" onClick={(e) => e.stopPropagation()}>
                      <div className="att-status-label">
                        <span>Roll Call Status:</span>
                        {isChecked && (
                          <span style={{
                            color: currentStatus === "PRESENT" ? "#059669" : currentStatus === "LATE" ? "#d97706" : currentStatus === "ABSENT" ? "#dc2626" : "#7c3aed",
                            fontWeight: 800
                          }}>
                            {currentStatus}
                          </span>
                        )}
                      </div>
                      <div className="att-status-pills">
                        {[
                          { key: "PRESENT", icon: "✅", label: "Present", color: "#10b981", bg: "#ecfdf5" },
                          { key: "LATE", icon: "⚠️", label: "Late", color: "#f59e0b", bg: "#fffbeb" },
                          { key: "ABSENT", icon: "❌", label: "Absent", color: "#ef4444", bg: "#fef2f2" },
                          { key: "EXCUSED", icon: "ℹ️", label: "Excused", color: "#8b5cf6", bg: "#f5f3ff" },
                        ].map((st) => {
                          const active = isChecked && currentStatus === st.key;
                          return (
                            <button
                              key={st.key}
                              type="button"
                              className={`att-status-btn ${active ? "active" : ""}`}
                              style={{
                                borderColor: active ? st.color : "#cbd5e1",
                                background: active ? st.bg : "#ffffff",
                                color: active ? st.color : "#64748b",
                                fontWeight: active ? 700 : 500,
                              }}
                              onClick={() => {
                                if (!isChecked) toggle(s.id);
                                setStatus(s.id, st.key);
                              }}
                            >
                              <span>{st.icon}</span> <span>{st.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* If in Departure mode */}
                  {isDeparture && rec?.departure_time && (
                    <div className="att-card-sub-info">
                      <span>Departed: <strong>{fmtTime(rec.departure_time)}</strong></span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Saved Records Table */}
      {existingRecords.length > 0 && (
        <div className="panel table-panel">
          <div className="panel-head">
            <div>
              <h3>Attendance Log — {selectedDate}</h3>
              <p>{existingRecords.length} record(s) saved for this date</p>
            </div>
            <button className="secondary btn-sm" onClick={loadAttendance}><RefreshCw size={14} /> Refresh</button>
          </div>

          {/* Desktop Table View */}
          <div className="attendance-desktop-table table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Arrival Time</th>
                  <th>Departure Time</th>
                  <th>Status</th>
                  <th>Method</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {existingRecords.map((r) => {
                  const stu = students.find((s) => s.id === r.student_id);
                  const sFullName = stu
                    ? [stu.first_name, stu.middle_name, stu.last_name].filter(Boolean).join(" ")
                    : `Student #${r.student_id}`;
                  const nameWithCode = stu ? `${sFullName} (${stu.student_code})` : sFullName;
                  return (
                    <tr key={r.id}>
                      <td><strong>{nameWithCode}</strong></td>
                      <td style={{ color: r.arrival_time ? "#059669" : "var(--muted)", fontWeight: 600 }}>{fmtTime(r.arrival_time)}</td>
                      <td style={{ color: r.departure_time ? "#d97706" : "var(--muted)", fontWeight: 600 }}>{fmtTime(r.departure_time)}</td>
                      <td><span className={`status ${r.status?.toLowerCase()}`}>{r.status}</span></td>
                      <td>{r.arrival_method || r.departure_method || ""}</td>
                      <td>
                        <div className="action-btns">
                          <button
                            className="btn-sm-edit"
                            onClick={() => setEditAttendance({ record: r, studentName: nameWithCode })}
                          >
                            <Pencil size={13} /> Edit
                          </button>
                          <button
                            className="btn-sm-danger"
                            onClick={() => setDeleteAttendance({ id: r.id, studentName: nameWithCode })}
                          >
                            <Trash2 size={13} /> Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards View for Log */}
          <div className="attendance-mobile-cards">
            {existingRecords.map((r) => {
              const stu = students.find((s) => s.id === r.student_id);
              const sFullName = stu
                ? [stu.first_name, stu.middle_name, stu.last_name].filter(Boolean).join(" ")
                : `Student #${r.student_id}`;
              const nameWithCode = stu ? `${sFullName} (${stu.student_code})` : sFullName;
              return (
                <div key={r.id} className="att-log-card">
                  <div className="att-log-card-header">
                    <div className="att-log-card-name">{nameWithCode}</div>
                    <span className={`status ${r.status?.toLowerCase()}`}>{r.status}</span>
                  </div>
                  <div className="att-log-card-times">
                    <div>Arrival: <strong style={{ color: r.arrival_time ? "#059669" : "#64748b" }}>{fmtTime(r.arrival_time) || "N/A"}</strong></div>
                    <div>Departure: <strong style={{ color: r.departure_time ? "#d97706" : "#64748b" }}>{fmtTime(r.departure_time) || "N/A"}</strong></div>
                    {r.arrival_method && <div>Via: {r.arrival_method}</div>}
                  </div>
                  <div className="att-log-card-actions">
                    <button
                      className="btn-sm-edit"
                      onClick={() => setEditAttendance({ record: r, studentName: nameWithCode })}
                    >
                      <Pencil size={13} /> Edit
                    </button>
                    <button
                      className="btn-sm-danger"
                      onClick={() => setDeleteAttendance({ id: r.id, studentName: nameWithCode })}
                    >
                      <Trash2 size={13} /> Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {editAttendance && (
        <EditAttendanceModal
          key={editAttendance.record.id}
          record={editAttendance.record}
          studentName={editAttendance.studentName}
          onClose={() => setEditAttendance(null)}
          onSaved={(msg) => {
            loadAttendance();
            setSaveResult({ success: true, message: msg || "Attendance record updated successfully" });
          }}
        />
      )}

      {deleteAttendance && (
        <ConfirmModal
          title="Delete Attendance Record"
          message={`Are you sure you want to permanently delete the attendance record for "${deleteAttendance.studentName}" on ${selectedDate}?`}
          onConfirm={handleDeleteAttendance}
          onClose={() => setDeleteAttendance(null)}
          loading={deleteLoading}
        />
      )}
    </div>
  );
}
/*  Parents Page  */

function ParentsView({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [students, setStudents] = useState([]);
  const [links, setLinks] = useState([]);
  const [modalAddParent, setModalAddParent] = useState(false);
  const [modalLinkStudent, setModalLinkStudent] = useState(false);
  const [selectedParentForTelegram, setSelectedParentForTelegram] = useState(null);
  const [editParent, setEditParent] = useState(null);
  const [deleteParent, setDeleteParent] = useState(null);
  const [editLink, setEditLink] = useState(null);
  const [unlinkTarget, setUnlinkTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [myChildren, setMyChildren] = useState([]);
  const [search, setSearch] = useState("");
  const [testResult, setTestResult] = useState(null);
  const [testingId, setTestingId] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const load = (msg) => {
    api.get("/api/users/").then((r) => setUsers(r.data.filter((u) => u.role === "PARENT"))).catch(() => { });
    api.get("/api/students/").then((r) => setStudents(r.data)).catch(() => { });
    api.get("/api/parents/links").then((r) => setLinks(r.data)).catch(() => []);
    if (currentUser?.role === "PARENT") {
      api.get("/api/parents/my-children").then((r) => setMyChildren(r.data)).catch(() => { });
    }
    if (msg) setFeedback({ type: "success", message: msg });
  };
  useEffect(() => { load(); }, [currentUser]);

  const handleDeleteParent = async () => {
    if (!deleteParent) return;
    const name = deleteParent.full_name;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/users/${deleteParent.id}`);
      setDeleteParent(null);
      load(`Parent account "${name}" deleted successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to delete parent account" });
      setDeleteParent(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleUnlink = async () => {
    if (!unlinkTarget) return;
    const { student_name, parent_name } = unlinkTarget;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/parents/links/${unlinkTarget.id}`);
      setUnlinkTarget(null);
      load(`Unlinked student "${student_name}" from guardian "${parent_name}" successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to unlink student" });
      setUnlinkTarget(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleSendTest = async (parent) => {
    setTestingId(parent.id);
    setTestResult(null);
    try {
      const res = await api.post(`/api/notifications/test/${parent.id}`);
      setTestResult({ success: true, message: `✅ Success: Sent test alert to ${parent.full_name}'s Telegram (ID: ${parent.telegram_id})` });
    } catch (err) {
      setTestResult({
        success: false,
        message: `❌ Telegram Alert Failed: ${err.response?.data?.detail || err.message}`,
        failedParent: parent
      });
    } finally {
      setTestingId(null);
    }
  };

  // Group links by parent_id
  const parentLinksMap = {};
  links.forEach((lk) => {
    if (!parentLinksMap[lk.parent_id]) parentLinksMap[lk.parent_id] = [];
    parentLinksMap[lk.parent_id].push(lk);
  });

  const filtered = users.filter((u) => {
    const q = search.toLowerCase();
    const nameMatch = u.full_name.toLowerCase().includes(q);
    const emailMatch = (u.email && u.email.toLowerCase().includes(q));
    const phoneMatch = (u.phone && u.phone.includes(q));
    const childMatch = (parentLinksMap[u.id] || []).some((lk) => lk.student_name.toLowerCase().includes(q) || lk.student_code.toLowerCase().includes(q));
    return nameMatch || emailMatch || phoneMatch || childMatch;
  });

  return (
    <div>
      {modalAddParent && <CreateUserModal onClose={() => setModalAddParent(false)} onSaved={() => load("Parent account registered successfully")} />}
      {modalLinkStudent && <LinkStudentModal parents={users} students={students} onClose={() => setModalLinkStudent(false)} onSaved={() => load("Student linked to parent successfully")} />}
      {selectedParentForTelegram && (
        <LinkTelegramModal parent={selectedParentForTelegram} onClose={() => setSelectedParentForTelegram(null)} onSaved={() => load("Telegram account linked successfully")} />
      )}
      {editParent && (
        <EditUserModal key={editParent.id} user={editParent} onClose={() => setEditParent(null)} onSaved={(msg) => load(msg || "Parent profile updated successfully")} />
      )}
      {editLink && (
        <EditParentLinkModal key={editLink.id} link={editLink} onClose={() => setEditLink(null)} onSaved={(msg) => load(msg || "Guardian relationship updated successfully")} />
      )}
      {deleteParent && (
        <ConfirmModal
          title="Delete Parent Account"
          message={`Are you sure you want to permanently delete parent "${deleteParent.full_name}"? All associated student links and notification subscriptions will be removed.`}
          onConfirm={handleDeleteParent}
          onClose={() => setDeleteParent(null)}
          loading={deleteLoading}
        />
      )}
      {unlinkTarget && (
        <ConfirmModal
          title="Unlink Student"
          message={`Unlink student "${unlinkTarget.student_name}" from guardian "${unlinkTarget.parent_name}"?`}
          onConfirm={handleUnlink}
          onClose={() => setUnlinkTarget(null)}
          loading={deleteLoading}
        />
      )}

      {currentUser?.role === "PARENT" && (
        <div className="panel" style={{ marginBottom: 24 }}>
          <div className="panel-head">
            <div>
              <h3>My Linked Children</h3>
              <p>Students associated with your parent account</p>
            </div>
            <span className="pill success">{myChildren.length} Linked</span>
          </div>
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Student Name</th>
                  <th>Class</th>
                </tr>
              </thead>
              <tbody>
                {myChildren.map((c) => (
                  <tr key={c.id}>
                    <td><strong>{c.student_code}</strong></td>
                    <td>{c.name}</td>
                    <td>{c.class_id ? `Class #${c.class_id}` : "Unassigned"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!myChildren.length && <div className="empty">No students are currently linked to your profile. Contact your school admin.</div>}
          </div>
        </div>
      )}

      <div className="page-heading">
        <div>
          <div className="eyebrow">FAMILY & NOTIFICATIONS</div>
          <h2>Parents & Guardians</h2>
          <p>Manage guardian profiles, child linkages, Telegram connectivity, and test alerts.</p>
        </div>
        <div className="header-actions">
          <button className="secondary" onClick={() => setModalLinkStudent(true)}><Link2 size={16} /> Link Student</button>
          <button className="primary" onClick={() => setModalAddParent(true)}><Plus size={16} /> Add Parent</button>
        </div>
      </div>

      <AlertBanner feedback={feedback} onClose={() => setFeedback(null)} />
      {testResult && (
        <div
          className={testResult.success ? "modal-success" : "error"}
          style={{
            marginBottom: 16,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 10
          }}
        >
          <span>{testResult.message}</span>
          {!testResult.success && testResult.failedParent && (
            <button
              type="button"
              className="btn-sm"
              style={{
                background: "#fee2e2",
                color: "#991b1b",
                border: "1px solid #f87171",
                cursor: "pointer",
                padding: "4px 12px",
                borderRadius: 4,
                fontWeight: 600,
                display: "inline-flex",
                alignItems: "center",
                gap: 6
              }}
              onClick={() => handleSendTest(testResult.failedParent)}
              disabled={testingId === testResult.failedParent.id}
            >
              <RotateCcw size={13} className={testingId === testResult.failedParent.id ? "spin" : ""} /> Retry Test Alert
            </button>
          )}
        </div>
      )}

      <div className="panel table-panel">
        <div className="table-toolbar">
          <div className="searchbox">
            <Search size={16} />
            <input placeholder="Filter parents or children..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <span className="pill info">{filtered.length} Parents</span>
        </div>
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Parent Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Linked Children</th>
                <th>Telegram Sync</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => {
                const childLinks = parentLinksMap[p.id] || [];
                return (
                  <tr key={p.id}>
                    <td><strong>{p.full_name}</strong></td>
                    <td>{p.email || "—"}</td>
                    <td>{p.phone || "—"}</td>
                    <td>
                      {childLinks.length > 0 ? (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                          {childLinks.map((lk) => (
                            <span
                              key={lk.id}
                              style={{
                                background: "#f0fdf4", color: "#166534",
                                border: "1px solid #bbf7d0", borderRadius: 6,
                                padding: "2px 8px", fontSize: 12, fontWeight: 600,
                                display: "inline-flex", alignItems: "center", gap: 4
                              }}
                            >
                              <span
                                onClick={() => setEditLink(lk)}
                                style={{ cursor: "pointer" }}
                                title="Click to edit link relationship"
                              >
                                {lk.student_name} ({lk.relationship_type})
                              </span>
                              <button
                                className="chip-remove"
                                title="Unlink student"
                                onClick={() => setUnlinkTarget(lk)}
                              >
                                ✕
                              </button>
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span style={{ fontSize: 12, color: "var(--muted)" }}>No children linked</span>
                      )}
                    </td>
                    <td>
                      {p.telegram_id ? (
                        <span className="status present">
                          Linked ({p.telegram_username ? `@${p.telegram_username}` : `ID: ${p.telegram_id}`})
                        </span>
                      ) : (
                        <span className="status absent">Not Linked</span>
                      )}
                    </td>
                    <td>
                      <div className="action-btns">
                        <button className="secondary btn-sm" onClick={() => setSelectedParentForTelegram(p)}>
                          <Send size={13} /> {p.telegram_id ? "TG" : "Link TG"}
                        </button>
                        {p.telegram_id && (
                          <button
                            className="accent-btn btn-sm"
                            onClick={() => handleSendTest(p)}
                            disabled={testingId === p.id}
                          >
                            <Send size={13} /> {testingId === p.id ? "..." : "Test"}
                          </button>
                        )}
                        <button className="btn-sm-edit" onClick={() => setEditParent(p)}>
                          <Pencil size={13} /> Edit
                        </button>
                        <button className="btn-sm-danger" onClick={() => { setFeedback(null); setDeleteParent(p); }}>
                          <Trash2 size={13} /> Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!filtered.length && <div className="empty">No parents found.</div>}
        </div>
      </div>
    </div>
  );
}

/*  Users Page  */
function UsersView({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [modal, setModal] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [deleteUser, setDeleteUser] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [search, setSearch] = useState("");

  const load = (msg) => {
    api.get("/api/users/").then((r) => setUsers(r.data)).catch(() => { });
    if (msg) setFeedback({ type: "success", message: msg });
  };
  useEffect(() => { load(); }, []);

  const handleDeleteUser = async () => {
    if (!deleteUser) return;
    const name = deleteUser.full_name;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/users/${deleteUser.id}`);
      setDeleteUser(null);
      load(`User "${name}" deleted successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to delete user" });
      setDeleteUser(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  const filtered = users.filter((u) =>
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.role.toLowerCase().includes(search.toLowerCase()) ||
    (u.email && u.email.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div>
      {modal && <CreateUserModal onClose={() => setModal(false)} onSaved={() => load("User account registered successfully")} />}
      {editUser && <EditUserModal key={editUser.id} user={editUser} onClose={() => setEditUser(null)} onSaved={(msg) => load(msg || "User account updated successfully")} />}
      {deleteUser && (
        <ConfirmModal
          title="Delete User Account"
          message={`Are you sure you want to permanently delete user "${deleteUser.full_name}" (${deleteUser.role})?`}
          onConfirm={handleDeleteUser}
          onClose={() => setDeleteUser(null)}
          loading={deleteLoading}
        />
      )}

      <div className="page-heading">
        <div>
          <div className="eyebrow">ACCESS CONTROL</div>
          <h2>System User Accounts</h2>
          <p>Manage administrators, teachers, security officers, and guardians.</p>
        </div>
        <button className="primary" onClick={() => setModal(true)}><UserPlus size={16} /> Register User</button>
      </div>

      <AlertBanner feedback={feedback} onClose={() => setFeedback(null)} />

      <div className="panel table-panel">
        <div className="table-toolbar">
          <div className="searchbox">
            <Search size={16} />
            <input placeholder="Search users by name or role..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <span className="pill info">{filtered.length} Users</span>
        </div>
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Telegram ID</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id}>
                  <td><strong>{u.full_name}</strong></td>
                  <td><span className="badge-role">{u.role}</span></td>
                  <td>{u.email || "—"}</td>
                  <td>{u.phone || "—"}</td>
                  <td>{u.telegram_id ? `${u.telegram_id} (${u.telegram_username ? `@${u.telegram_username}` : ""})` : "—"}</td>
                  <td><span className="status present">{u.status || "ACTIVE"}</span></td>
                  <td>
                    <div className="action-btns">
                      <button className="btn-sm-edit" onClick={() => setEditUser(u)}>
                        <Pencil size={13} /> Edit
                      </button>
                      <button
                        className="btn-sm-danger"
                        onClick={() => { setFeedback(null); setDeleteUser(u); }}
                        disabled={u.id === currentUser?.id}
                        title={u.id === currentUser?.id ? "Cannot delete your own active account" : "Delete user"}
                      >
                        <Trash2 size={13} /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!filtered.length && <div className="empty">No users found.</div>}
        </div>
      </div>
    </div>
  );
}

/*  Notification Settings & Logs Page  */
function NotificationsView() {
  const [students, setStudents] = useState([]);
  const [logs, setLogs] = useState([]);
  const [modal, setModal] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(false);
  const [deleteLog, setDeleteLog] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [resendingId, setResendingId] = useState(null);
  const [bulkResending, setBulkResending] = useState(false);

  const loadLogs = (msg) => {
    setLoadingLogs(true);
    api.get("/api/notifications/logs")
      .then((r) => {
        setLogs(r.data);
        if (msg) setFeedback({ type: "success", message: msg });
      })
      .catch((err) => {
        if (msg) setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to refresh logs" });
      })
      .finally(() => setLoadingLogs(false));
  };

  useEffect(() => {
    api.get("/api/students/").then((r) => setStudents(r.data)).catch(() => { });
    loadLogs();
  }, []);

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === logs.length && logs.length > 0) {
      setSelectedIds([]);
    } else {
      setSelectedIds(logs.map((l) => l.id));
    }
  };

  const handleResendSingle = async (log) => {
    setResendingId(log.id);
    setFeedback(null);
    try {
      const { data } = await api.post(`/api/notifications/resend/${log.id}`);
      loadLogs(data.message || `Notification #${log.id} resent successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to resend notification" });
    } finally {
      setResendingId(null);
    }
  };

  const handleBulkResend = async () => {
    if (!selectedIds.length) return;
    setBulkResending(true);
    setFeedback(null);
    try {
      const { data } = await api.post("/api/notifications/bulk-resend", { ids: selectedIds });
      loadLogs(data.message || `Resent ${selectedIds.length} notification(s)`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to resend notifications" });
    } finally {
      setBulkResending(false);
    }
  };

  const handleRetryAllFailed = async () => {
    setBulkResending(true);
    setFeedback(null);
    try {
      const { data } = await api.post("/api/notifications/retry-all-failed");
      loadLogs(data.message || "Retry of failed notifications completed");
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to retry notifications" });
    } finally {
      setBulkResending(false);
    }
  };

  const handleBulkDelete = async () => {
    if (!selectedIds.length) return;
    const count = selectedIds.length;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      const { data } = await api.post("/api/notifications/bulk-delete", { ids: selectedIds });
      setConfirmBulkDelete(false);
      setSelectedIds([]);
      loadLogs(data.message || `Deleted ${count} notification record(s) successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to delete selected notifications" });
      setConfirmBulkDelete(false);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleDeleteSingle = async () => {
    if (!deleteLog) return;
    const title = deleteLog.title || `Notification #${deleteLog.id}`;
    setDeleteLoading(true);
    setFeedback(null);
    try {
      await api.delete(`/api/notifications/${deleteLog.id}`);
      const id = deleteLog.id;
      setDeleteLog(null);
      setSelectedIds((prev) => prev.filter((x) => x !== id));
      loadLogs(`Notification "${title}" deleted successfully`);
    } catch (err) {
      setFeedback({ type: "error", message: err.response?.data?.detail || "Failed to delete notification record" });
      setDeleteLog(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div>
      {modal && <NotificationSettingsModal students={students} onClose={() => setModal(false)} />}

      {confirmBulkDelete && (
        <ConfirmModal
          title="Delete Notifications in Bulk"
          message={`Are you sure you want to permanently delete the ${selectedIds.length} selected notification log record(s)? This action cannot be undone.`}
          onConfirm={handleBulkDelete}
          onClose={() => setConfirmBulkDelete(false)}
          loading={deleteLoading}
        />
      )}

      {deleteLog && (
        <ConfirmModal
          title="Delete Notification Log"
          message={`Are you sure you want to permanently delete notification "${deleteLog.title}" (ID: ${deleteLog.id})?`}
          onConfirm={handleDeleteSingle}
          onClose={() => setDeleteLog(null)}
          loading={deleteLoading}
        />
      )}

      <div className="page-heading">
        <div>
          <div className="eyebrow">COMMUNICATION & AUDIT</div>
          <h2>Notification Settings & Bot Logs</h2>
          <p>Configure alert triggers and inspect real-time Telegram delivery history.</p>
        </div>
        <div className="header-actions">
          <button className="secondary" onClick={() => loadLogs()}><RefreshCw size={15} /> Refresh Logs</button>
          <button className="primary" onClick={() => setModal(true)}><Settings size={16} /> Configure Rules</button>
        </div>
      </div>

      <AlertBanner feedback={feedback} onClose={() => setFeedback(null)} />

      <div className="panel table-panel" style={{ marginBottom: 24 }}>
        <div className="table-toolbar" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <strong>Recent Telegram Delivery Logs</strong>
            <span className="pill info">{logs.length} Logged Events</span>
            {selectedIds.length > 0 && (
              <span className="pill" style={{ background: "#ede9fe", color: "#6366f1", fontWeight: 600 }}>
                {selectedIds.length} Selected
              </span>
            )}
            {logs.some((l) => l.status === "FAILED") && (
              <button
                type="button"
                className="btn-sm"
                style={{
                  background: "#fef3c7",
                  color: "#92400e",
                  border: "1px solid #fcd34d",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  fontWeight: 600,
                  padding: "5px 12px",
                  borderRadius: 6,
                  cursor: "pointer"
                }}
                onClick={handleRetryAllFailed}
                disabled={bulkResending}
                title="Retry delivering all failed notifications"
              >
                <RotateCcw size={13} className={bulkResending ? "spin" : ""} /> Retry All Failed ({logs.filter((l) => l.status === "FAILED").length})
              </button>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            {selectedIds.length > 0 && (
              <>
                <button
                  type="button"
                  className="btn-sm"
                  style={{
                    background: "#e0e7ff",
                    color: "#3730a3",
                    border: "1px solid #c7d2fe",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    fontWeight: 600,
                    padding: "6px 14px",
                    borderRadius: 6,
                    cursor: "pointer",
                    boxShadow: "0 1px 2px rgba(0,0,0,0.05)"
                  }}
                  onClick={handleBulkResend}
                  disabled={bulkResending}
                  title="Resend selected notifications"
                >
                  <RotateCcw size={14} className={bulkResending ? "spin" : ""} /> Resend Selected ({selectedIds.length})
                </button>
                <button
                  type="button"
                  className="btn-sm"
                  style={{
                    background: "#fee2e2",
                    color: "#b91c1c",
                    border: "1px solid #fca5a5",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    fontWeight: 600,
                    padding: "6px 14px",
                    borderRadius: 6,
                    cursor: "pointer",
                    boxShadow: "0 1px 2px rgba(0,0,0,0.05)"
                  }}
                  onClick={() => setConfirmBulkDelete(true)}
                  disabled={deleteLoading}
                >
                  <Trash2 size={15} /> Delete Selected ({selectedIds.length})
                </button>
                <button
                  type="button"
                  className="secondary btn-sm"
                  onClick={() => setSelectedIds([])}
                >
                  Clear Selection
                </button>
              </>
            )}
          </div>
        </div>
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th style={{ width: 44, textAlign: "center" }}>
                  <input
                    type="checkbox"
                    aria-label="Select all notifications"
                    checked={logs.length > 0 && selectedIds.length === logs.length}
                    onChange={toggleSelectAll}
                    style={{ cursor: "pointer", width: 16, height: 16 }}
                  />
                </th>
                <th>Time</th>
                <th>Type</th>
                <th>Title</th>
                <th>Message Snippet</th>
                <th>Status</th>
                <th>Delivery Error / Details</th>
                <th style={{ width: 90, textAlign: "center" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const checked = selectedIds.includes(log.id);
                return (
                  <tr
                    key={log.id}
                    style={{
                      backgroundColor: checked ? "rgba(99, 102, 241, 0.08)" : undefined,
                      transition: "background-color 0.15s ease"
                    }}
                  >
                    <td style={{ width: 44, textAlign: "center" }}>
                      <input
                        type="checkbox"
                        aria-label={`Select notification ${log.id}`}
                        checked={checked}
                        onChange={() => toggleSelect(log.id)}
                        style={{ cursor: "pointer", width: 16, height: 16 }}
                      />
                    </td>
                    <td>{log.created_at ? new Date(log.created_at).toLocaleString() : ""}</td>
                    <td><span className="badge-role">{log.type}</span></td>
                    <td><strong>{log.title}</strong></td>
                    <td style={{ maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{log.message}</td>
                    <td>
                      <span className={`status ${log.status === "SENT" ? "present" : log.status === "FAILED" ? "absent" : "late"}`}>
                        {log.status}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, color: log.error_message ? "#b91c1c" : "#64748b" }}>
                      {log.error_message || (log.status === "SENT" ? "Delivered to Telegram " : "Pending worker dispatch")}
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <div style={{ display: "inline-flex", gap: 6, alignItems: "center", justifyContent: "center" }}>
                        <button
                          type="button"
                          className="btn-sm"
                          title="Resend notification to parent"
                          onClick={() => handleResendSingle(log)}
                          disabled={resendingId === log.id}
                          style={{
                            padding: "5px 8px",
                            background: log.status === "FAILED" ? "#fef3c7" : "#f1f5f9",
                            color: log.status === "FAILED" ? "#b45309" : "#475569",
                            border: log.status === "FAILED" ? "1px solid #fde68a" : "1px solid #cbd5e1",
                            borderRadius: 4,
                            cursor: "pointer",
                            display: "inline-flex",
                            alignItems: "center"
                          }}
                        >
                          <RotateCcw size={13} className={resendingId === log.id ? "spin" : ""} />
                        </button>
                        <button
                          type="button"
                          className="btn-sm-danger"
                          title="Delete notification log"
                          onClick={() => setDeleteLog(log)}
                          style={{ padding: "5px 8px" }}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!logs.length && <div className="empty">No notification records found in history yet.</div>}
        </div>
      </div>

      <div className="panel-grid">
        <div className="panel">
          <h3>Alert Triggers Supported</h3>
          <p style={{ color: "#64748b", fontSize: 13, margin: "8px 0 20px" }}>
            The SchoolGuard Telegram daemon monitors the following attendance events:
          </p>
          <div style={{ display: "grid", gap: 14 }}>
            {[
              { title: "Arrival Alerts", desc: "Instantly sends a message with exact arrival timestamp." },
              { title: "Departure Alerts", desc: "Notifies parents when the child checks out at the gate." },
              { title: "Late Arrival Alerts", desc: "Triggers if check-in is later than official class start time." },
              { title: "Absence Alerts", desc: "Dispatched if student remains unmarked past morning roll call." },
              { title: "School End Alerts", desc: "Sent at school closing bell." }
            ].map((item, idx) => (
              <div key={idx} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <CheckCircle2 size={18} color="#10b981" style={{ marginTop: 2 }} />
                <div>
                  <strong style={{ fontSize: 13 }}>{item.title}</strong>
                  <p style={{ fontSize: 12, color: "#64748b", margin: "2px 0 0" }}>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <h3>Telegram Bot Link Guide</h3>
          <p style={{ color: "#64748b", fontSize: 13, margin: "8px 0 16px" }}>
            How parents connect with the bot (<strong>@Felege_Selam_bot</strong>):
          </p>
          <ol style={{ fontSize: 13, color: "#475569", paddingLeft: 20, lineHeight: 1.7 }}>
            <li>Open Telegram and search for <code>@Felege_Selam_bot</code>.</li>
            <li>Press <strong>/start</strong> to initiate the chat.</li>
            <li>Press <strong>/link</strong> and enter your SchoolGuard email & password.</li>
            <li>Or from this dashboard, enter the parent's numeric Telegram Chat ID.</li>
            <li>Once linked, use the <strong>"Test Bot Alert"</strong> button on the Parents page to test delivery.</li>
          </ol>
        </div>
      </div>
    </div>
  );
}

/* 
   AUTH & BOOTSTRAP VIEWS
*/

function AuthShell({ onLoginSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "bootstrap"
  const [form, setForm] = useState({ email: "", password: "", full_name: "", phone: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function handleLogin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/login", { email: form.email, password: form.password });
      if (!data?.access_token) {
        throw new Error("Invalid response received from server. Please check your backend connection.");
      }
      localStorage.setItem("schoolguard_token", data.access_token);
      onLoginSuccess();
    } catch (err) {
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === "string") {
          setError(detail);
        } else if (Array.isArray(detail)) {
          setError(detail.map(d => d.msg).join(", "));
        } else {
          setError("Invalid credentials");
        }
      } else if (err.code === "ERR_NETWORK" || !err.response) {
        const targetUrl = api.defaults?.baseURL || "backend";
        setError(`Unable to connect to backend server at ${targetUrl}. Make sure the backend server is running with --host 0.0.0.0.`);
      } else {
        setError(err.message || "Invalid email or password");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleBootstrap(e) {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      await api.post("/api/auth/bootstrap-admin", {
        full_name: form.full_name,
        email: form.email,
        phone: form.phone,
        password: form.password,
        role: "ADMIN"
      });
      setSuccess("Administrator successfully bootstrapped! You can now log in.");
      setMode("login");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to bootstrap admin");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <div className="login-art">
        <div className="brand-mark"><ShieldCheck size={38} /></div>
        <h1>SchoolGuard</h1>
        <p>Comprehensive School Attendance, Parent Real-Time Notification & Gate Management Platform.</p>
        <div className="alert-card" style={{ background: "rgba(255, 255, 255, 0.08)", border: "1px solid rgba(255, 255, 255, 0.15)", marginTop: 40 }}>
          <CheckCircle2 size={24} color="#38bdf8" />
          <div>
            <strong style={{ color: "#fff" }}>Secure Gate Check-In & Sync</strong>
            <p style={{ color: "#94a3b8" }}>Every check-in is logged with cryptographic QR tokens and timestamped events.</p>
          </div>
        </div>
      </div>

      <div className="login-card">
        <div className="eyebrow">{mode === "login" ? "STAFF & PARENT PORTAL" : "SYSTEM SETUP"}</div>
        <h2>{mode === "login" ? "Sign in to SchoolGuard" : "Bootstrap Initial Admin"}</h2>
        <p className="muted">
          {mode === "login"
            ? "Enter your credentials to control and inspect the system."
            : "First-time setup: initialize the root Administrator account."}
        </p>

        {success && <div className="modal-success">{success}</div>}
        {error && <div className="error">{error}</div>}

        {mode === "login" ? (
          <form onSubmit={handleLogin}>
            <label>
              Email, Username or Phone
              <input type="text" value={form.email} onChange={(e) => set("email", e.target.value)} required />
            </label>
            <label>
              Password
              <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required />
            </label>
            <button className="primary full" disabled={loading}>{loading ? "Verifying" : "Sign in"}</button>

            <div className="login-footer-switch">
              Need first-time setup? <button type="button" onClick={() => { setError(""); setMode("bootstrap"); }}>Bootstrap Root Admin</button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleBootstrap}>
            <label>
              Admin Full Name *
              <input value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required />
            </label>
            <label>
              Admin Email *
              <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
            </label>
            <label>
              Phone
              <input value={form.phone} onChange={(e) => set("phone", e.target.value)} />
            </label>
            <label>
              Master Password *
              <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required />
            </label>
            <button className="primary full" disabled={loading}>{loading ? "Bootstrapping" : "Create Administrator"}</button>

            <div className="login-footer-switch">
              Already initialized? <button type="button" onClick={() => { setError(""); setMode("login"); }}>Back to Login</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

/* 
   MAIN APPLICATION CONTAINER
    */
export default function App() {
  const [authed, setAuthed] = useState(!!localStorage.getItem("schoolguard_token"));
  const [currentUser, setCurrentUser] = useState(null);
  const [page, setPage] = useState("dashboard");
  const [mobile, setMobile] = useState(false);
  const [modalSelfTelegram, setModalSelfTelegram] = useState(false);

  const fetchCurrentUser = () => {
    if (localStorage.getItem("schoolguard_token")) {
      api.get("/api/users/me")
        .then((r) => setCurrentUser(r.data))
        .catch(() => {
          localStorage.removeItem("schoolguard_token");
          setAuthed(false);
        });
    }
  };

  useEffect(() => {
    if (authed) fetchCurrentUser();
  }, [authed]);

  if (!authed) {
    return <AuthShell onLoginSuccess={() => setAuthed(true)} />;
  }

  return (
    <div className="app-shell">
      {modalSelfTelegram && (
        <SelfLinkTelegramModal
          currentUser={currentUser}
          onClose={() => setModalSelfTelegram(false)}
          onSaved={fetchCurrentUser}
        />
      )}

      {/*  Sidebar Navigation  */}
      <aside className={`sidebar ${mobile ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-icon"><ShieldCheck size={22} /></div>
          <span>School<span>Guard</span></span>
          <button className="close-mobile" onClick={() => setMobile(false)}><X /></button>
        </div>

        {/* User Chip */}
        <div className="user-chip">
          <div className="user-avatar">
            {currentUser?.full_name ? currentUser.full_name.slice(0, 2).toUpperCase() : "SG"}
          </div>
          <div>
            <strong>{currentUser?.full_name || "User"}</strong>
            <small>
              <span className="badge-role">{currentUser?.role || "STAFF"}</span>
            </small>
          </div>
        </div>

        <nav>
          <div className="nav-category">Main Navigation</div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={page === item.key ? "active" : ""}
                onClick={() => {
                  setPage(item.key);
                  setMobile(false);
                }}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <button onClick={() => setModalSelfTelegram(true)}>
            <Send size={16} /> Link My Telegram
          </button>
          <button onClick={() => { localStorage.removeItem("schoolguard_token"); setAuthed(false); }}>
            <LogOut size={16} /> Sign Out
          </button>
        </div>
      </aside>

      {/*  Main Content Area  */}
      <main className="main">
        <header className="topbar">
          <div className="top-left-status">
            <button className="menu-mobile" onClick={() => setMobile(true)}><Menu size={22} /></button>
            <div className="system-pill">
              <span className="dot" />
              API Connected (:8000)
            </div>
          </div>

          <div className="top-actions">
            <button className="secondary btn-sm" onClick={() => setModalSelfTelegram(true)}>
              <Send size={14} />
              {currentUser?.telegram_id ? `TG: ${currentUser.telegram_username ? `@${currentUser.telegram_username}` : currentUser.telegram_id}` : "Link Telegram"}
            </button>
          </div>
        </header>

        <section className="content">
          {page === "dashboard" && <DashboardView onNavigate={(p) => setPage(p)} />}
          {page === "schools" && <SchoolsView />}
          {page === "classes" && <ClassesView />}
          {page === "teachers" && <TeachersView />}
          {page === "students" && <StudentsView />}
          {page === "attendance" && <AttendanceView />}
          {page === "parents" && <ParentsView currentUser={currentUser} />}
          {page === "users" && <UsersView currentUser={currentUser} />}
          {page === "notifications" && <NotificationsView />}
        </section>
      </main>
    </div>
  );
}

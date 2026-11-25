"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { clearAccessToken, getAccessToken, type CurrentUser } from "@/lib/auth";
import { getCurrentUser } from "@/services/auth";
import QRScanner from "@/components/QRScanner";
import {
  getAttendanceHistory,
  getAttendanceSummary,
  getStudentSessions,
  verifyAttendance,
  type AttendanceHistory,
  type AttendanceSummary,
  type StudentSession,
} from "@/services/studentAttendance";

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function secondsRemaining(value: string): number {
  return Math.max(0, Math.ceil((new Date(value).getTime() - Date.now()) / 1000));
}

export default function StudentDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [sessions, setSessions] = useState<StudentSession[]>([]);
  const [history, setHistory] = useState<AttendanceHistory[]>([]);
  const [summary, setSummary] = useState<AttendanceSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<number | "">("");
  const [qrToken, setQrToken] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [, setTick] = useState(Date.now());

  const selectedSession = useMemo(
    () => sessions.find((session) => session.id === selectedSessionId) ?? null,
    [sessions, selectedSessionId],
  );

  async function loadDashboard(token: string) {
    const [currentUser, activeSessions, attendanceHistory, attendanceSummary] =
      await Promise.all([
        getCurrentUser(token),
        getStudentSessions(token),
        getAttendanceHistory(token),
        getAttendanceSummary(token),
      ]);

    if (currentUser.role !== "student") {
      router.replace("/" + currentUser.role);
      return;
    }

    setUser(currentUser);
    setSessions(activeSessions);
    setHistory(attendanceHistory);
    setSummary(attendanceSummary);

    if (
      selectedSessionId === "" ||
      !activeSessions.some((session) => session.id === selectedSessionId)
    ) {
      setSelectedSessionId(activeSessions[0]?.id ?? "");
    }
  }

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    loadDashboard(token)
      .catch(() => {
        clearAccessToken();
        router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  useEffect(() => {
    const interval = window.setInterval(() => setTick(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedSession) return;
    if (secondsRemaining(selectedSession.expires_at) === 0) {
      const token = getAccessToken();
      if (token) {
        getStudentSessions(token).then(setSessions).catch(() => undefined);
      }
    }
  }, [selectedSession, setTick]);

  function logout() {
    clearAccessToken();
    router.replace("/login");
  }

  async function submitVerification(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    const token = getAccessToken();
    if (!token || selectedSessionId === "" || !qrToken.trim() || !/^\d{6}$/.test(totpCode)) {
      setError("Select an active session, scan the QR code, and enter its 6-digit TOTP.");
      return;
    }

    setSubmitting(true);
    try {
      await verifyAttendance(token, selectedSessionId, qrToken.trim(), totpCode);
      setMessage("Attendance verified successfully.");
      setQrToken("");
      setTotpCode("");
      await loadDashboard(token);
    } catch (verificationError) {
      setError(
        verificationError instanceof Error
          ? verificationError.message
          : "Attendance verification failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !user) {
    return <main style={styles.loading}>Checking your SmartAttend session…</main>;
  }

  return (
    <main style={styles.page}>
      <div style={styles.container}>
        <header style={styles.header}>
          <div>
            <p style={styles.eyebrow}>SmartAttend • Student</p>
            <h1 style={styles.title}>Attendance verification</h1>
            <p style={styles.muted}>
              Signed in as <strong>{user.university_id}</strong>. Only your enrolled
              courses are available for verification.
            </p>
          </div>
          <button onClick={logout} style={styles.secondaryButton}>Sign out</button>
        </header>

        <section style={styles.grid}>
          <div style={styles.card}>
            <h2 style={styles.sectionTitle}>Verify attendance</h2>

            {sessions.length === 0 ? (
              <div style={styles.empty}>
                <strong>No active attendance session</strong>
                <span>Ask your lecturer to start the session for your enrolled unit.</span>
              </div>
            ) : (
              <>
                <label style={styles.label}>
                  Active unit
                  <select
                    value={selectedSessionId}
                    onChange={(event) => {
                      setSelectedSessionId(Number(event.target.value));
                      setQrToken("");
                      setTotpCode("");
                      setMessage(null);
                      setError(null);
                    }}
                    style={styles.input}
                  >
                    {sessions.map((session) => (
                      <option key={session.id} value={session.id}>
                        {session.course_code} — {session.course_name}
                      </option>
                    ))}
                  </select>
                </label>

                {selectedSession && (
                  <p style={styles.sessionInfo}>
                    Session ends in <strong>{secondsRemaining(selectedSession.expires_at)}s</strong>.
                    The verification window rotates every {selectedSession.refresh_interval_seconds}s.
                  </p>
                )}

                <QRScanner onDetected={setQrToken} />

                <form onSubmit={submitVerification} style={styles.form}>
                  <label style={styles.label}>
                    QR token
                    <input
                      value={qrToken}
                      onChange={(event) => setQrToken(event.target.value)}
                      placeholder="Scan the QR or paste its token"
                      style={styles.input}
                      autoComplete="off"
                    />
                  </label>

                  <label style={styles.label}>
                    6-digit TOTP
                    <input
                      value={totpCode}
                      onChange={(event) => setTotpCode(event.target.value.replace(/D/g, "").slice(0, 6))}
                      placeholder="000000"
                      inputMode="numeric"
                      maxLength={6}
                      style={styles.input}
                      autoComplete="one-time-code"
                    />
                  </label>

                  <button disabled={submitting} style={styles.primaryButton}>
                    {submitting ? "Verifying…" : "Verify attendance"}
                  </button>
                </form>
              </>
            )}

            {message && <p style={styles.success}>{message}</p>}
            {error && <p style={styles.error}>{error}</p>}
          </div>

          <div style={styles.card}>
            <h2 style={styles.sectionTitle}>Attendance summary</h2>
            {summary.length === 0 ? (
              <p style={styles.muted}>No enrolled units found.</p>
            ) : (
              <div style={styles.list}>
                {summary.map((item) => (
                  <div key={item.course_id} style={styles.summaryRow}>
                    <div>
                      <strong>{item.course_code}</strong>
                      <span style={styles.small}>{item.course_name}</span>
                    </div>
                    <strong>{item.percentage.toFixed(1)}%</strong>
                  </div>
                ))}
              </div>
            )}

            <h2 style={{ ...styles.sectionTitle, marginTop: 28 }}>Recent attendance</h2>
            {history.length === 0 ? (
              <p style={styles.muted}>No attendance records yet.</p>
            ) : (
              <div style={styles.list}>
                {history.slice(0, 8).map((item) => (
                  <div key={item.id} style={styles.historyRow}>
                    <div>
                      <strong>{item.course_code}</strong>
                      <span style={styles.small}>{item.course_name}</span>
                    </div>
                    <span style={styles.small}>{formatDate(item.recorded_at)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

const styles = {
  loading: {
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    fontFamily: "Arial, sans-serif",
  },
  page: {
    minHeight: "100vh",
    padding: 24,
    boxSizing: "border-box" as const,
    fontFamily: "Arial, sans-serif",
    background: "#f6f7fb",
  },
  container: {
    width: "min(1120px, 100%)",
    margin: "0 auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 20,
    marginBottom: 24,
  },
  eyebrow: {
    margin: "0 0 8px",
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    color: "#667085",
  },
  title: {
    margin: 0,
    fontSize: "clamp(28px, 4vw, 42px)",
    color: "#172033",
  },
  muted: { color: "#667085", lineHeight: 1.6 },
  grid: {
    display: "grid",
    gridTemplateColumns: "minmax(0, 1.15fr) minmax(320px, 0.85fr)",
    gap: 20,
  },
  card: {
    background: "#ffffff",
    borderRadius: 20,
    padding: 24,
    boxShadow: "0 10px 30px rgba(15, 23, 42, 0.07)",
  },
  sectionTitle: { margin: "0 0 18px", fontSize: 22, color: "#172033" },
  label: { display: "grid", gap: 8, marginBottom: 16, fontWeight: 700, color: "#344054" },
  input: {
    width: "100%",
    boxSizing: "border-box" as const,
    border: "1px solid #d0d5dd",
    borderRadius: 10,
    padding: "12px 13px",
    fontSize: 15,
    background: "#ffffff",
  },
  form: { marginTop: 18 },
  primaryButton: {
    width: "100%",
    border: 0,
    borderRadius: 10,
    padding: "13px 16px",
    background: "#172033",
    color: "#ffffff",
    fontWeight: 700,
    cursor: "pointer",
  },
  secondaryButton: {
    border: "1px solid #d0d5dd",
    borderRadius: 10,
    padding: "10px 14px",
    background: "#ffffff",
    cursor: "pointer",
  },
  sessionInfo: {
    margin: "0 0 16px",
    padding: 12,
    borderRadius: 10,
    background: "#f2f4f7",
    color: "#475467",
    lineHeight: 1.5,
  },
  empty: {
    display: "grid",
    gap: 8,
    padding: 18,
    borderRadius: 12,
    background: "#f9fafb",
    color: "#667085",
  },
  success: {
    marginTop: 16,
    padding: 12,
    borderRadius: 10,
    background: "#ecfdf3",
    color: "#067647",
  },
  error: {
    marginTop: 16,
    padding: 12,
    borderRadius: 10,
    background: "#fef3f2",
    color: "#b42318",
    lineHeight: 1.5,
  },
  list: { display: "grid", gap: 10 },
  summaryRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: 16,
    padding: 14,
    border: "1px solid #eaecf0",
    borderRadius: 12,
  },
  historyRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: 16,
    padding: 14,
    borderBottom: "1px solid #eaecf0",
  },
  small: {
    display: "block",
    marginTop: 4,
    color: "#667085",
    fontSize: 13,
    lineHeight: 1.4,
  },
};

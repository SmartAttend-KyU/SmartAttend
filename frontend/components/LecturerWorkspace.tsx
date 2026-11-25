"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  clearAccessToken,
  getAccessToken,
  rolePath,
  type CurrentUser,
} from "@/lib/auth";
import { getCurrentUser } from "@/services/auth";
import {
  createAttendanceSession,
  endAttendanceSession,
  getAttendanceSession,
  getLecturerCourses,
  type AttendanceSession,
  type LecturerCourse,
} from "@/services/attendance";

export default function LecturerWorkspace() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [courses, setCourses] = useState<LecturerCourse[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | "">("");
  const [durationMinutes, setDurationMinutes] = useState(15);
  const [refreshInterval, setRefreshInterval] = useState(10);
  const [session, setSession] = useState<AttendanceSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [ending, setEnding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const logout = useCallback(() => {
    clearAccessToken();
    router.replace("/login");
  }, [router]);

  useEffect(() => {
    const accessToken = getAccessToken();
    if (!accessToken) {
      router.replace("/login");
      return;
    }

    setToken(accessToken);
    getCurrentUser(accessToken)
      .then(async (currentUser) => {
        if (currentUser.role !== "lecturer") {
          router.replace(rolePath(currentUser.role));
          return;
        }

        setUser(currentUser);
        const assignedCourses = await getLecturerCourses(accessToken);
        setCourses(assignedCourses);
        if (assignedCourses.length > 0) {
          setSelectedCourseId(assignedCourses[0].id);
        }
      })
      .catch(() => {
        clearAccessToken();
        router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const refreshLiveSession = useCallback(async () => {
    if (!token || !session) return;

    try {
      const latest = await getAttendanceSession(token, session.id);
      setSession(latest);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not refresh the session.");
    }
  }, [token, session]);

  useEffect(() => {
    if (!token || !session || session.status !== "active" || !session.qr_expires_at) {
      return;
    }

    const delay = Math.max(
      250,
      new Date(session.qr_expires_at).getTime() - Date.now() + 100,
    );
    const timer = window.setTimeout(refreshLiveSession, delay);
    return () => window.clearTimeout(timer);
  }, [token, session, refreshLiveSession]);

  async function startSession() {
    if (!token || selectedCourseId === "") return;

    setStarting(true);
    setError(null);
    try {
      const created = await createAttendanceSession(token, {
        course_id: selectedCourseId,
        duration_minutes: durationMinutes,
        refresh_interval_seconds: refreshInterval,
      });
      setSession(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start attendance session.");
    } finally {
      setStarting(false);
    }
  }

  async function stopSession() {
    if (!token || !session) return;

    setEnding(true);
    setError(null);
    try {
      const ended = await endAttendanceSession(token, session.id);
      setSession(ended);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not end attendance session.");
    } finally {
      setEnding(false);
    }
  }

  const sessionSecondsRemaining = useMemo(() => {
    if (!session) return 0;
    return Math.max(0, Math.ceil((new Date(session.expires_at).getTime() - now) / 1000));
  }, [session, now]);

  const qrSecondsRemaining = useMemo(() => {
    if (!session?.qr_expires_at || session.status !== "active") return 0;
    return Math.max(0, Math.ceil((new Date(session.qr_expires_at).getTime() - now) / 1000));
  }, [session, now]);

  if (loading || !user) {
    return (
      <main style={styles.page}>
        <section style={styles.card}>Checking your SmartAttend session…</section>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <section style={styles.shell}>
        <header style={styles.header}>
          <div>
            <p style={styles.eyebrow}>SmartAttend · Lecturer</p>
            <h1 style={styles.title}>Attendance session</h1>
            <p style={styles.subtitle}>
              {user.university_id} · {user.email}
            </p>
          </div>
          <button onClick={logout} style={styles.secondaryButton}>Sign out</button>
        </header>

        {error && <div role="alert" style={styles.error}>{error}</div>}

        {!session || session.status !== "active" ? (
          <div style={styles.setup}>
            <div>
              <h2 style={styles.sectionTitle}>Start a class attendance session</h2>
              <p style={styles.muted}>
                Only courses assigned to your lecturer account are available.
                The verification window defaults to 10 seconds and can be set from 5–15 seconds.
              </p>
            </div>

            <label style={styles.label}>
              Unit / course
              <select
                value={selectedCourseId}
                onChange={(event) => setSelectedCourseId(event.target.value ? Number(event.target.value) : "")}
                style={styles.input}
                disabled={courses.length === 0}
              >
                {courses.length === 0 ? (
                  <option value="">No assigned courses</option>
                ) : (
                  courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.code} — {course.name}
                    </option>
                  ))
                )}
              </select>
            </label>

            <div style={styles.grid}>
              <label style={styles.label}>
                Session duration
                <select
                  value={durationMinutes}
                  onChange={(event) => setDurationMinutes(Number(event.target.value))}
                  style={styles.input}
                >
                  {[5, 10, 15, 30, 45, 60, 90, 120].map((minutes) => (
                    <option key={minutes} value={minutes}>{minutes} minutes</option>
                  ))}
                </select>
              </label>

              <label style={styles.label}>
                QR / TOTP refresh
                <select
                  value={refreshInterval}
                  onChange={(event) => setRefreshInterval(Number(event.target.value))}
                  style={styles.input}
                >
                  {[5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15].map((seconds) => (
                    <option key={seconds} value={seconds}>{seconds} seconds</option>
                  ))}
                </select>
              </label>
            </div>

            <button
              onClick={startSession}
              disabled={starting || selectedCourseId === "" || courses.length === 0}
              style={styles.primaryButton}
            >
              {starting ? "Starting…" : "Start attendance session"}
            </button>
          </div>
        ) : (
          <div style={styles.live}>
            <div style={styles.sessionBar}>
              <div>
                <p style={styles.eyebrow}>Live session</p>
                <h2 style={styles.courseTitle}>{session.course_code} — {session.course_name}</h2>
              </div>
              <button onClick={stopSession} disabled={ending} style={styles.dangerButton}>
                {ending ? "Ending…" : "End session"}
              </button>
            </div>

            <div style={styles.liveGrid}>
              <div style={styles.qrPanel}>
                {session.qr_code && (
                  <img
                    src={session.qr_code}
                    alt="Rotating SmartAttend attendance QR code"
                    style={styles.qr}
                  />
                )}
                <p style={styles.timerLabel}>QR refreshes in</p>
                <div style={styles.timer}>{qrSecondsRemaining}s</div>
                <p style={styles.muted}>
                  The QR token is server-signed and valid only for the current
                  verification window, with a short network-latency grace period.
                </p>
              </div>

              <div style={styles.totpPanel}>
                <p style={styles.timerLabel}>6-digit TOTP</p>
                <div aria-label="Current six digit TOTP" style={styles.totp}>
                  {session.totp_code ?? "------"}
                </div>
                <p style={styles.timerLabel}>Session time remaining</p>
                <div style={styles.sessionTimer}>{sessionSecondsRemaining}s</div>
                <div style={styles.infoBox}>
                  <strong>Verification window</strong>
                  <span>{session.refresh_interval_seconds} seconds</span>
                  <span>Session ends at {new Date(session.expires_at).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <footer style={styles.footer}>
          SmartAttend does not claim to prove physical presence. It verifies the
          time-bound session credentials defined by the project proposal.
        </footer>
      </section>
    </main>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    padding: 24,
    boxSizing: "border-box" as const,
    background: "#f5f7fb",
  },
  shell: {
    width: "min(1100px, 100%)",
    margin: "0 auto",
    background: "#ffffff",
    borderRadius: 24,
    padding: 32,
    boxShadow: "0 12px 40px rgba(15, 23, 42, 0.08)",
    boxSizing: "border-box" as const,
  },
  card: {
    width: "min(720px, 100%)",
    margin: "15vh auto 0",
    background: "#ffffff",
    borderRadius: 20,
    padding: 32,
    boxShadow: "0 12px 40px rgba(15, 23, 42, 0.08)",
    boxSizing: "border-box" as const,
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 20,
    paddingBottom: 24,
    borderBottom: "1px solid #e7eaf0",
  },
  eyebrow: {
    margin: "0 0 8px",
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    color: "#5b6475",
  },
  title: { margin: 0, fontSize: 34, lineHeight: 1.1 },
  subtitle: { margin: "8px 0 0", color: "#667085" },
  secondaryButton: {
    border: "1px solid #d7dce5",
    background: "#ffffff",
    borderRadius: 10,
    padding: "10px 14px",
    cursor: "pointer",
  },
  error: {
    marginTop: 20,
    padding: 14,
    borderRadius: 12,
    background: "#fff4f2",
    border: "1px solid #f4c7c1",
    color: "#9f2d20",
  },
  setup: { display: "grid", gap: 20, paddingTop: 28 },
  sectionTitle: { margin: 0, fontSize: 24 },
  label: { display: "grid", gap: 8, fontWeight: 700, fontSize: 14 },
  input: {
    width: "100%",
    boxSizing: "border-box" as const,
    border: "1px solid #d7dce5",
    borderRadius: 10,
    padding: "12px 14px",
    background: "#ffffff",
    fontSize: 15,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 16,
  },
  primaryButton: {
    border: 0,
    borderRadius: 12,
    padding: "13px 18px",
    background: "#172033",
    color: "#ffffff",
    fontWeight: 700,
    cursor: "pointer",
    fontSize: 15,
  },
  dangerButton: {
    border: "1px solid #e3a39b",
    borderRadius: 10,
    padding: "10px 14px",
    background: "#fff7f5",
    color: "#9f2d20",
    fontWeight: 700,
    cursor: "pointer",
  },
  live: { paddingTop: 28 },
  sessionBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 20,
  },
  courseTitle: { margin: 0, fontSize: 24 },
  liveGrid: {
    display: "grid",
    gridTemplateColumns: "minmax(280px, 1fr) minmax(280px, 1fr)",
    gap: 24,
    marginTop: 24,
  },
  qrPanel: {
    display: "grid",
    justifyItems: "center",
    padding: 24,
    borderRadius: 18,
    background: "#f7f8fb",
  },
  qr: {
    width: "min(360px, 100%)",
    aspectRatio: "1 / 1",
    background: "#ffffff",
    borderRadius: 12,
    padding: 12,
    boxSizing: "border-box" as const,
  },
  totpPanel: {
    display: "grid",
    alignContent: "center",
    justifyItems: "center",
    padding: 24,
    borderRadius: 18,
    border: "1px solid #e7eaf0",
  },
  timerLabel: {
    margin: "0 0 8px",
    color: "#667085",
    fontWeight: 700,
    fontSize: 13,
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
  },
  timer: { fontSize: 34, fontWeight: 800, marginBottom: 12 },
  sessionTimer: { fontSize: 28, fontWeight: 800, marginBottom: 20 },
  totp: {
    fontSize: 56,
    letterSpacing: "0.18em",
    fontWeight: 900,
    fontVariantNumeric: "tabular-nums",
    margin: "12px 0 28px",
  },
  infoBox: {
    width: "100%",
    display: "grid",
    gap: 6,
    padding: 16,
    borderRadius: 12,
    background: "#f7f8fb",
    boxSizing: "border-box" as const,
  },
  muted: { margin: 0, color: "#667085", lineHeight: 1.55, textAlign: "center" as const },
  footer: {
    marginTop: 28,
    paddingTop: 20,
    borderTop: "1px solid #e7eaf0",
    color: "#667085",
    fontSize: 13,
    lineHeight: 1.5,
  },
};

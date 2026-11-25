"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, rolePath, setAccessToken } from "@/lib/auth";
import { getCurrentUser, login } from "@/services/auth";

export default function LoginPage() {
  const router = useRouter();
  const [universityId, setUniversityId] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    getCurrentUser(token)
      .then((user) => router.replace(rolePath(user.role)))
      .catch(() => undefined);
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setSubmitting(true);

    try {
      const tokenResponse = await login(universityId, password);
      setAccessToken(tokenResponse.access_token);

      const user = await getCurrentUser(tokenResponse.access_token);
      router.replace(rolePath(user.role));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main style={styles.page}>
      <section style={styles.card}>
        <div>
          <p style={styles.eyebrow}>Kirinyaga University prototype</p>
          <h1 style={styles.title}>Welcome to SmartAttend</h1>
          <p style={styles.subtitle}>
            Sign in with your university ID to access the correct SmartAttend workspace.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            University ID
            <input
              value={universityId}
              onChange={(event) => setUniversityId(event.target.value)}
              autoComplete="username"
              placeholder="e.g. STU001"
              required
              minLength={2}
              maxLength={64}
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              placeholder="Enter your password"
              required
              minLength={8}
              maxLength={128}
              style={styles.input}
            />
          </label>

          {message && (
            <p role="alert" style={styles.error}>
              {message}
            </p>
          )}

          <button type="submit" disabled={submitting} style={styles.button}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div style={styles.demoBox}>
          <strong>Demo accounts</strong>
          <span>Admin: ADMIN001</span>
          <span>Lecturer: LECT001</span>
          <span>Student: STU001</span>
          <span>Password: ChangeMe123!</span>
        </div>
      </section>
    </main>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    padding: 24,
    background: "#f5f7fb",
    boxSizing: "border-box" as const,
  },
  card: {
    width: "min(480px, 100%)",
    background: "#ffffff",
    borderRadius: 20,
    padding: 32,
    boxShadow: "0 12px 40px rgba(15, 23, 42, 0.08)",
    boxSizing: "border-box" as const,
  },
  eyebrow: {
    margin: "0 0 8px",
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    color: "#5b6475",
  },
  title: {
    margin: 0,
    fontSize: 34,
    lineHeight: 1.15,
  },
  subtitle: {
    margin: "12px 0 0",
    color: "#5b6475",
    lineHeight: 1.6,
  },
  form: {
    display: "grid",
    gap: 18,
    marginTop: 28,
  },
  label: {
    display: "grid",
    gap: 8,
    fontWeight: 600,
  },
  input: {
    width: "100%",
    boxSizing: "border-box" as const,
    padding: "12px 13px",
    border: "1px solid #d7dce5",
    borderRadius: 10,
    fontSize: 16,
  },
  button: {
    border: 0,
    borderRadius: 10,
    padding: "12px 16px",
    fontWeight: 700,
    fontSize: 16,
    cursor: "pointer",
    background: "#172033",
    color: "#ffffff",
  },
  error: {
    margin: 0,
    padding: 12,
    borderRadius: 10,
    background: "#fff2f2",
    color: "#a51d2d",
  },
  demoBox: {
    display: "grid",
    gap: 5,
    marginTop: 28,
    padding: 14,
    borderRadius: 12,
    background: "#f7f8fb",
    color: "#5b6475",
    fontSize: 14,
  },
};

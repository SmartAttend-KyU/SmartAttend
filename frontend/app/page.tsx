"use client";

import { FormEvent, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function HomePage() {
  const [sessionId, setSessionId] = useState("");
  const [code, setCode] = useState("");
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");

  async function verifyAttendance(event: FormEvent) {
    event.preventDefault();
    setMessage("Verifying…");
    try {
      const response = await fetch(`${apiUrl}/api/attendance/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: Number(sessionId),
          verification_code: code,
        }),
      });
      const data = await response.json();
      setMessage(response.ok ? "Attendance recorded successfully." : data.detail ?? "Verification failed.");
    } catch {
      setMessage("Unable to reach the SmartAttend API.");
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "64px 24px" }}>
      <section style={{ background: "white", borderRadius: 16, padding: 32, boxShadow: "0 8px 30px rgba(0,0,0,.06)" }}>
        <h1 style={{ marginTop: 0 }}>SmartAttend</h1>
        <p>Secure, server-verified class attendance using short-lived rotating codes.</p>
        <form onSubmit={verifyAttendance} style={{ display: "grid", gap: 16, marginTop: 28 }}>
          <label>
            Access token
            <input value={token} onChange={(e) => setToken(e.target.value)} required style={{ display: "block", width: "100%", padding: 10, marginTop: 6, boxSizing: "border-box" }} />
          </label>
          <label>
            Session ID
            <input type="number" min="1" value={sessionId} onChange={(e) => setSessionId(e.target.value)} required style={{ display: "block", width: "100%", padding: 10, marginTop: 6, boxSizing: "border-box" }} />
          </label>
          <label>
            Verification code
            <input inputMode="numeric" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} required style={{ display: "block", width: "100%", padding: 10, marginTop: 6, boxSizing: "border-box" }} />
          </label>
          <button type="submit" style={{ padding: 12, border: 0, borderRadius: 8, cursor: "pointer" }}>
            Verify attendance
          </button>
        </form>
        {message && <p role="status" style={{ marginTop: 20 }}>{message}</p>}
      </section>
    </main>
  );
}

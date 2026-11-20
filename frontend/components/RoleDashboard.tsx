"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  clearAccessToken,
  getAccessToken,
  rolePath,
  type CurrentUser,
  type UserRole,
} from "@/lib/auth";
import { getCurrentUser } from "@/services/auth";

interface RoleDashboardProps {
  expectedRole: UserRole;
  title: string;
  description: string;
}

export default function RoleDashboard({
  expectedRole,
  title,
  description,
}: RoleDashboardProps) {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    getCurrentUser(token)
      .then((currentUser) => {
        if (currentUser.role !== expectedRole) {
          router.replace(rolePath(currentUser.role));
          return;
        }
        setUser(currentUser);
      })
      .catch(() => {
        clearAccessToken();
        router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [expectedRole, router]);

  function logout() {
    clearAccessToken();
    router.replace("/login");
  }

  if (loading || !user) {
    return (
      <main style={styles.page}>
        <section style={styles.card}>Checking your SmartAttend session…</section>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <section style={styles.card}>
        <div style={styles.header}>
          <div>
            <p style={styles.eyebrow}>SmartAttend</p>
            <h1 style={styles.title}>{title}</h1>
          </div>
          <button onClick={logout} style={styles.secondaryButton}>
            Sign out
          </button>
        </div>

        <div style={styles.userBox}>
          <strong>{user.university_id}</strong>
          <span>{user.email}</span>
          <span style={{ textTransform: "capitalize" }}>{user.role}</span>
        </div>

        <p style={styles.description}>{description}</p>
        <p style={styles.note}>
          Authentication is complete. The next milestone will add the full role-specific attendance dashboard.
        </p>
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
    boxSizing: "border-box" as const,
    background: "#f5f7fb",
  },
  card: {
    width: "min(720px, 100%)",
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
  },
  eyebrow: {
    margin: "0 0 8px",
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    color: "#5b6475",
  },
  title: {
    margin: 0,
    fontSize: 32,
    lineHeight: 1.15,
  },
  secondaryButton: {
    border: "1px solid #d7dce5",
    background: "#ffffff",
    borderRadius: 10,
    padding: "10px 14px",
    cursor: "pointer",
  },
  userBox: {
    display: "grid",
    gap: 4,
    marginTop: 28,
    padding: 18,
    borderRadius: 14,
    background: "#f7f8fb",
  },
  description: {
    marginTop: 24,
    fontSize: 17,
    lineHeight: 1.6,
  },
  note: {
    marginTop: 24,
    color: "#5b6475",
    lineHeight: 1.6,
  },
};

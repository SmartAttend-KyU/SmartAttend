import { api } from "@/lib/api";

export interface LecturerCourse {
  id: number;
  code: string;
  name: string;
}

export interface AttendanceSession {
  id: number;
  course_id: number;
  course_code: string;
  course_name: string;
  starts_at: string;
  expires_at: string;
  ended_at: string | null;
  refresh_interval_seconds: number;
  status: "active" | "expired" | "ended";
  totp_code: string | null;
  qr_token: string | null;
  qr_code: string | null;
  qr_expires_at: string | null;
}

function withAuth(token: string, init: RequestInit = {}): RequestInit {
  return {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      Authorization: "Bearer " + token,
    },
  };
}

export async function getLecturerCourses(token: string): Promise<LecturerCourse[]> {
  return api<LecturerCourse[]>("/api/attendance/courses", withAuth(token));
}

export async function createAttendanceSession(
  token: string,
  payload: {
    course_id: number;
    duration_minutes: number;
    refresh_interval_seconds: number;
  },
): Promise<AttendanceSession> {
  return api<AttendanceSession>(
    "/api/attendance/sessions",
    withAuth(token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  );
}

export async function getAttendanceSession(
  token: string,
  sessionId: number,
): Promise<AttendanceSession> {
  return api<AttendanceSession>(
    "/api/attendance/sessions/" + sessionId,
    withAuth(token),
  );
}

export async function endAttendanceSession(
  token: string,
  sessionId: number,
): Promise<AttendanceSession> {
  return api<AttendanceSession>(
    "/api/attendance/sessions/" + sessionId + "/end",
    withAuth(token, { method: "POST" }),
  );
}

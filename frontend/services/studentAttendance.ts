const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface StudentSession {
  id: number;
  course_id: number;
  course_code: string;
  course_name: string;
  starts_at: string;
  expires_at: string;
  refresh_interval_seconds: number;
  status: "active";
}

export interface AttendanceHistory {
  id: number;
  session_id: number;
  course_id: number;
  course_code: string;
  course_name: string;
  recorded_at: string;
  verification_method: string;
}

export interface AttendanceSummary {
  course_id: number;
  course_code: string;
  course_name: string;
  attended_sessions: number;
  total_sessions: number;
  percentage: number;
}

export interface AttendanceResult {
  id: number;
  session_id: number;
  student_id: number;
  recorded_at: string;
  verification_method: string;
}

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API_URL + path, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
      ...(init?.headers ?? {}),
    },
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.detail ?? "Request failed.");
  }
  return body as T;
}

export function getStudentSessions(token: string): Promise<StudentSession[]> {
  return request<StudentSession[]>("/api/attendance/student/sessions", token);
}

export function getAttendanceHistory(token: string): Promise<AttendanceHistory[]> {
  return request<AttendanceHistory[]>("/api/attendance/student/history", token);
}

export function getAttendanceSummary(token: string): Promise<AttendanceSummary[]> {
  return request<AttendanceSummary[]>("/api/attendance/student/summary", token);
}

export function verifyAttendance(
  token: string,
  sessionId: number,
  qrToken: string,
  totpCode: string,
): Promise<AttendanceResult> {
  return request<AttendanceResult>("/api/attendance/verify", token, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      qr_token: qrToken,
      totp_code: totpCode,
    }),
  });
}

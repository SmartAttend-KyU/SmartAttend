export type UserRole = "student" | "lecturer" | "admin";

export interface CurrentUser {
  id: number;
  university_id: string;
  email: string;
  role: UserRole;
}

const TOKEN_KEY = "smartattend_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

export function rolePath(role: UserRole): string {
  return `/${role}`;
}

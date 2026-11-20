import type { CurrentUser } from "@/lib/auth";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface LoginResponse {
  access_token: string;
  token_type: string;
}

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return data.detail ?? "Request failed.";
  } catch {
    return "Request failed.";
  }
}

export async function login(universityId: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${apiUrl}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      university_id: universityId.trim(),
      password,
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json();
}

export async function getCurrentUser(token: string): Promise<CurrentUser> {
  const response = await fetch(`${apiUrl}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json();
}

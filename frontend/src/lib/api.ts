const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function getHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = { ...(extra || {}) };
  if (typeof window !== "undefined") {
    const storedKey = localStorage.getItem("cardguard_api_key");
    const key = storedKey || process.env.NEXT_PUBLIC_API_KEY;
    if (key) headers["X-API-Key"] = key;
  } else if (process.env.NEXT_PUBLIC_API_KEY) {
    headers["X-API-Key"] = process.env.NEXT_PUBLIC_API_KEY;
  }
  return headers;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: getHeaders(
      init?.body instanceof FormData
        ? (init?.headers as Record<string, string> | undefined)
        : { "Content-Type": "application/json", ...(init?.headers as Record<string, string>) }
    ),
    cache: "no-store",
  });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const err = await res.json();
      if (err?.detail) msg = err.detail;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export function getApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

/** Simple in-memory per-user rate limiter (max N requests per window). */

interface WindowEntry {
  count: number;
  resetAt: number;
}

const store = new Map<string, WindowEntry>();

const DEFAULT_MAX_REQUESTS = 10;
const DEFAULT_WINDOW_MS = 60_000;

/** Checks if the given userId has exceeded the rate limit. Returns true if allowed, false if blocked. */
export function checkRateLimit(
  userId: string,
  maxRequests: number = DEFAULT_MAX_REQUESTS,
  windowMs: number = DEFAULT_WINDOW_MS
): boolean {
  const now = Date.now();
  const entry = store.get(userId);

  if (!entry || now >= entry.resetAt) {
    store.set(userId, { count: 1, resetAt: now + windowMs });
    return true;
  }

  if (entry.count >= maxRequests) {
    return false;
  }

  entry.count++;
  return true;
}

/** Stub session returned by getServerSession. Replaced by Module 1's real auth. */
export interface Session {
  userId: string;
}

/** Reads x-mock-user-id header from the incoming request to simulate an authenticated session.
 *  This is the ONLY file that needs changing when real auth (Module 1) is integrated.
 *  The function signature (Request => Session | null) must stay stable. */
export async function getServerSession(req: Request): Promise<Session | null> {
  const userId = req.headers.get("x-mock-user-id");
  if (!userId) return null;
  return { userId };
}

import { prisma } from "./prisma";

export class UserNotFoundError extends Error {
  constructor(userId: string) {
    super(`User not found: ${userId}`);
    this.name = "UserNotFoundError";
  }
}

/** Read-only access to the stub User model. Returns job and goal for prompt building. */
export async function getUserById(
  userId: string
): Promise<{ userJob: string; userGoal: string }> {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) {
    throw new UserNotFoundError(userId);
  }
  return { userJob: user.userJob, userGoal: user.userGoal };
}

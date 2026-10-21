import { prisma } from "./prisma";
import type { ChatMessage } from "../validation/schemas";

export interface ChatRecord {
  id: string;
  userId: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

/** Retrieves a user's most recent chat record, or null if none exists. */
export async function getByUserId(userId: string): Promise<ChatRecord | null> {
  const chat = await prisma.chat.findFirst({
    where: { userId },
    orderBy: { createdAt: "desc" },
  });
  if (!chat) return null;
  return {
    id: chat.id,
    userId: chat.userId,
    messages: chat.messages as unknown as ChatMessage[],
    createdAt: chat.createdAt,
    updatedAt: chat.updatedAt,
  };
}

/** Appends new messages to the user's Chat. Creates the Chat row if it doesn't exist yet. */
export async function appendMessages(
  userId: string,
  newMessages: ChatMessage[]
): Promise<ChatRecord> {
  const existing = await prisma.chat.findFirst({
    where: { userId },
    orderBy: { createdAt: "desc" },
  });

  if (existing) {
    const updated = await prisma.chat.update({
      where: { id: existing.id },
      data: {
        messages: [...(existing.messages as unknown as ChatMessage[]), ...newMessages],
      },
    });
    return {
      id: updated.id,
      userId: updated.userId,
      messages: updated.messages as unknown as ChatMessage[],
      createdAt: updated.createdAt,
      updatedAt: updated.updatedAt,
    };
  }

  const created = await prisma.chat.create({
    data: {
      userId,
      messages: newMessages as unknown as PrismaInputJson,
    },
  });

  return {
    id: created.id,
    userId: created.userId,
    messages: created.messages as unknown as ChatMessage[],
    createdAt: created.createdAt,
    updatedAt: created.updatedAt,
  };
}

// Helper type for Prisma's JSON input
type PrismaInputJson = ReturnType<typeof JSON.parse>;

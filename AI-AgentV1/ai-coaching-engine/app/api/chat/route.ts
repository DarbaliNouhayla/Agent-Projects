import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/auth/mockAuth";
import { ChatRequestSchema } from "@/lib/validation/schemas";
import { handleMessage } from "@/lib/services/chatService";
import { UserNotFoundError } from "@/lib/repositories/userRepository";
import { checkRateLimit } from "@/lib/rateLimiter";
import { logger } from "@/lib/logger";

export async function POST(request: Request) {
  try {
    const session = await getServerSession(request);
    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (!checkRateLimit(session.userId)) {
      return NextResponse.json(
        { error: "Too many requests, please slow down." },
        { status: 429 }
      );
    }

    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return NextResponse.json(
        { error: { message: "Invalid JSON body" } },
        { status: 400 }
      );
    }

    const parsed = ChatRequestSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.flatten() },
        { status: 400 }
      );
    }

    const { message, selected_context, chat_history } = parsed.data;

    const result = await handleMessage({
      userId: session.userId,
      message,
      context: selected_context,
      history: chat_history?.map((h) => ({
        role: h.role,
        content: h.content,
      })),
    });

    return NextResponse.json({
      message: result.message,
      suggestion: result.suggestion,
    });
  } catch (err) {
    if (err instanceof UserNotFoundError) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }
    logger.error("Unhandled error in POST /api/chat:", err);
    return NextResponse.json(
      {
        message: "Je rencontre un souci technique, réessaie dans un instant.",
        suggestion: "NONE",
      },
      { status: 200 }
    );
  }
}

import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/auth/mockAuth";
import { getByUserId } from "@/lib/repositories/chatRepository";
import { logger } from "@/lib/logger";

export async function GET(request: Request) {
  try {
    const session = await getServerSession(request);
    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const chat = await getByUserId(session.userId);

    return NextResponse.json({
      messages: chat?.messages ?? [],
    });
  } catch (err) {
    logger.error("Unhandled error in GET /api/chat/history:", err);
    return NextResponse.json({ messages: [] }, { status: 200 });
  }
}

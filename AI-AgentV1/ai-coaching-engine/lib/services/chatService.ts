import { getUserById, UserNotFoundError } from "../repositories/userRepository";
import { getByUserId, appendMessages } from "../repositories/chatRepository";
import { generateChatReply } from "../llm/llmProvider";
import type { ChatContext } from "../prompts/promptBuilder";
import type { ChatMessage } from "../validation/schemas";

export interface HandleMessageInput {
  userId: string;
  message: string;
  context: ChatContext;
  history?: ChatMessage[];
}

export interface HandleMessageResult {
  message: string;
  suggestion: "NONE" | "BOOKING_INTENT";
}

/** Orchestrates message handling: loads user, resolves history, builds prompt, calls LLM, persists. */
export async function handleMessage(
  input: HandleMessageInput
): Promise<HandleMessageResult> {
  const user = await getUserById(input.userId);

  let history: ChatMessage[];
  if (input.history) {
    history = input.history;
  } else {
    const chat = await getByUserId(input.userId);
    history = chat?.messages ?? [];
  }

  const llmHistory = history.map((m) => ({
    role: m.role as "user" | "assistant",
    content: m.content,
  }));

  const result = await generateChatReply({
    userJob: user.userJob,
    userGoal: user.userGoal,
    context: input.context,
    message: input.message,
    history: llmHistory,
  });

  const now = new Date().toISOString();

  const userMsg: ChatMessage = {
    role: "user",
    content: input.message,
    context: input.context,
    createdAt: now,
  };

  const assistantMsg: ChatMessage = {
    role: "assistant",
    content: result.message,
    context: input.context,
    suggestion: result.suggestion,
    ...(result.referralReason ? { referralReason: result.referralReason } : {}),
    ...(result.referralUrgency ? { referralUrgency: result.referralUrgency } : {}),
    createdAt: now,
  };

  await appendMessages(input.userId, [userMsg, assistantMsg]);

  return {
    message: result.message,
    suggestion: result.suggestion,
  };
}

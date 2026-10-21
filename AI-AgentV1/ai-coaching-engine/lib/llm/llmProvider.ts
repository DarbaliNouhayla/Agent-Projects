import { callGroq, LLMUnavailableError } from "./groqClient";
import { buildSystemPrompt, type ChatContext } from "../prompts/promptBuilder";
import type { ChatMessage } from "../validation/schemas";

export interface ChatResult {
  message: string;
  suggestion: "NONE" | "BOOKING_INTENT";
  referralReason?: string;
  referralUrgency?: "low" | "medium" | "high";
}

/** Calls the LLM with the assembled prompt and maps tool-calling output to the ChatResult shape. */
export async function generateChatReply(input: {
  userJob: string;
  userGoal: string;
  context: ChatContext;
  message: string;
  history: { role: "user" | "assistant"; content: string }[];
}): Promise<ChatResult> {
  const systemPrompt = buildSystemPrompt(input.userJob, input.userGoal, input.context);

  let raw;
  try {
    raw = await callGroq(systemPrompt, input.history, input.message);
  } catch (err) {
    if (err instanceof LLMUnavailableError) {
      return {
        message: "Je rencontre un souci technique, réessaie dans un instant.",
        suggestion: "NONE",
      };
    }
    throw err;
  }

  const toolCall = raw.toolCalls.find(
    (tc) => tc.function.name === "flag_expert_referral"
  );

  if (toolCall) {
    const args = JSON.parse(toolCall.function.arguments);
    const fallbackMessage =
      "Je pense qu'un accompagnement par un expert pourrait t'aider ici.";
    return {
      message: raw.content ?? fallbackMessage,
      suggestion: "BOOKING_INTENT",
      referralReason: args.reason,
      referralUrgency: args.urgency,
    };
  }

  return {
    message: raw.content ?? "",
    suggestion: "NONE",
  };
}

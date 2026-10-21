import { z } from "zod";

export const ChatContextEnum = z.enum(["personnel", "professionnel", "sante"]);
export type ChatContext = z.infer<typeof ChatContextEnum>;

export const ChatMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string(),
  context: ChatContextEnum.optional(),
  suggestion: z.enum(["NONE", "BOOKING_INTENT"]).optional(),
  referralReason: z.string().optional(),
  referralUrgency: z.enum(["low", "medium", "high"]).optional(),
  createdAt: z.string().optional(),
});
export type ChatMessage = z.infer<typeof ChatMessageSchema>;

export const ChatHistoryItemSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string(),
});

export const ChatRequestSchema = z.object({
  message: z.string().min(1).max(2000),
  selected_context: ChatContextEnum,
  chat_history: z.array(ChatHistoryItemSchema).optional(),
});
export type ChatRequest = z.infer<typeof ChatRequestSchema>;

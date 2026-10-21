import Groq from "groq-sdk";
import { env } from "@/lib/config/env";
import { FLAG_EXPERT_REFERRAL_TOOL } from "./toolsSchema";

export class LLMUnavailableError extends Error {
  constructor(cause: unknown) {
    super("LLM service is currently unavailable after exhausting retries");
    this.name = "LLMUnavailableError";
    this.cause = cause;
  }
}

export interface GroqToolCall {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
}

export interface GroqRawResponse {
  content: string | null;
  toolCalls: GroqToolCall[];
}

const groq = new Groq({ apiKey: env.GROQ_API_KEY });

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryableError(status: number): boolean {
  return status === 429 || status >= 500;
}

/** Wraps the Groq SDK chat completions call with retry, backoff, and typed errors.
 *  Retries on 429 (rate limit), 5xx, and network errors. Respects Retry-After header. */
export async function callGroq(
  systemPrompt: string,
  history: { role: "user" | "assistant"; content: string }[],
  userMessage: string
): Promise<GroqRawResponse> {
  const maxRetries = env.GROQ_MAX_RETRIES;
  const timeout = env.GROQ_TIMEOUT_MS;

  const messages: { role: "system" | "user" | "assistant"; content: string }[] = [
    { role: "system", content: systemPrompt },
    ...history.map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
    { role: "user", content: userMessage },
  ];

  let lastError: unknown;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await groq.chat.completions.create(
        {
          model: env.GROQ_MODEL,
          messages,
          tools: [FLAG_EXPERT_REFERRAL_TOOL],
          tool_choice: "auto",
        },
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      const choice = response.choices[0];
      const content = choice.message?.content ?? null;
      const toolCalls: GroqToolCall[] =
        (choice.message?.tool_calls as GroqToolCall[])?.map((tc) => ({
          id: tc.id,
          type: "function" as const,
          function: {
            name: tc.function.name,
            arguments: tc.function.arguments,
          },
        })) ?? [];

      return { content, toolCalls };
    } catch (err: unknown) {
      lastError = err;

      if (err instanceof Error && err.name === "AbortError") {
        throw new LLMUnavailableError(err);
      }

      if (typeof err === "object" && err !== null && "status" in err) {
        const typedErr = err as { status: number; headers?: Record<string, string> };
        if (!isRetryableError(typedErr.status)) {
          throw err;
        }
        if (attempt < maxRetries) {
          const retryAfter = typedErr.headers?.["retry-after"]
            ? parseInt(typedErr.headers["retry-after"], 10) * 1000
            : null;
          const delay = retryAfter ?? Math.min(500 * Math.pow(2, attempt), 10000);
          await sleep(delay);
          continue;
        }
      } else if (err instanceof Error && err.name === "LLMUnavailableError") {
        throw err;
      } else {
        // Network/transient error
        if (attempt < maxRetries) {
          const delay = Math.min(500 * Math.pow(2, attempt), 10000);
          await sleep(delay);
          continue;
        }
      }
    }
  }

  throw new LLMUnavailableError(lastError);
}

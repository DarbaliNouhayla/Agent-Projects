import { describe, it, expect, vi, beforeEach } from "vitest";
import { POST } from "../../app/api/chat/route";
import * as userRepository from "../../lib/repositories/userRepository";
import * as chatRepository from "../../lib/repositories/chatRepository";
import * as llmProvider from "../../lib/llm/llmProvider";

vi.mock("../../lib/repositories/userRepository", () => ({
  getUserById: vi.fn(),
  UserNotFoundError: class extends Error {
    constructor(userId: string) {
      super(`User not found: ${userId}`);
      this.name = "UserNotFoundError";
    }
  },
}));

vi.mock("../../lib/repositories/chatRepository", () => ({
  getByUserId: vi.fn(),
  appendMessages: vi.fn(),
}));

vi.mock("../../lib/llm/llmProvider", () => ({
  generateChatReply: vi.fn(),
}));

function buildRequest(overrides: {
  body?: unknown;
  userId?: string;
} = {}): Request {
  const headers = new Headers();
  if (overrides.userId !== undefined) {
    headers.set("x-mock-user-id", overrides.userId);
  }
  headers.set("Content-Type", "application/json");

  return new Request("http://localhost:3000/api/chat", {
    method: "POST",
    headers,
    body: overrides.body !== undefined ? JSON.stringify(overrides.body) : JSON.stringify({
      message: "Bonjour",
      selected_context: "personnel",
    }),
  });
}

describe("POST /api/chat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(userRepository.getUserById).mockResolvedValue({
      userJob: "développeur",
      userGoal: "productivité",
    });
    vi.mocked(chatRepository.appendMessages).mockResolvedValue({
      id: "chat-1",
      userId: "test-user",
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    });
    vi.mocked(llmProvider.generateChatReply).mockResolvedValue({
      message: "Bonjour ! Comment puis-je t'aider ?",
      suggestion: "NONE",
    });
  });

  it("returns 401 when x-mock-user-id header is missing", async () => {
    const req = buildRequest({ userId: undefined as unknown as string });
    const res = await POST(req);
    expect(res.status).toBe(401);
    const body = await res.json();
    expect(body.error).toBe("Unauthorized");
  });

  it("returns 400 when request body is missing required field (message)", async () => {
    const req = buildRequest({
      userId: "test-user",
      body: { selected_context: "personnel" },
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.error).toBeDefined();
  });

  it("returns 200 with correct shape for valid request", async () => {
    const req = buildRequest({
      userId: "test-user",
      body: {
        message: "J'ai besoin de conseils pour mieux gérer mon temps",
        selected_context: "personnel",
      },
    });
    const res = await POST(req);
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("message");
    expect(body).toHaveProperty("suggestion");
    expect(["NONE", "BOOKING_INTENT"]).toContain(body.suggestion);
  });

  it("persists messages to database", async () => {
    const req = buildRequest({
      userId: "test-user",
      body: {
        message: "Aide-moi à mieux communiquer avec mon équipe",
        selected_context: "professionnel",
      },
    });
    await POST(req);
    expect(chatRepository.appendMessages).toHaveBeenCalled();
  });

  it("returns BOOKING_INTENT when LLM triggers tool call", async () => {
    vi.mocked(llmProvider.generateChatReply).mockResolvedValue({
      message: "Un expert humain pourrait mieux t'aider.",
      suggestion: "BOOKING_INTENT",
    });

    const req = buildRequest({
      userId: "test-user",
      body: { message: "J'ai besoin d'un psy", selected_context: "sante" },
    });
    const res = await POST(req);
    const body = await res.json();
    expect(body.suggestion).toBe("BOOKING_INTENT");
  });

  it("accepts chat_history in the request body", async () => {
    const req = buildRequest({
      userId: "test-user",
      body: {
        message: "Et ensuite ?",
        selected_context: "personnel",
        chat_history: [
          { role: "user", content: "Bonjour" },
          { role: "assistant", content: "Bonjour !" },
        ],
      },
    });
    const res = await POST(req);
    expect(res.status).toBe(200);
  });

  it("validates message length constraint (max 2000 chars)", async () => {
    const req = buildRequest({
      userId: "test-user",
      body: {
        message: "x".repeat(2001),
        selected_context: "personnel",
      },
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
  });
});

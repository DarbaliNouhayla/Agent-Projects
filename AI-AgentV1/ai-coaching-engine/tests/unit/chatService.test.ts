import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleMessage } from "../../lib/services/chatService";
import type { ChatContext } from "../../lib/prompts/promptBuilder";

const mockUserRepo = vi.hoisted(() => ({
  getUserById: vi.fn(),
  UserNotFoundError: class extends Error {
    constructor(userId: string) {
      super(`User not found: ${userId}`);
      this.name = "UserNotFoundError";
    }
  },
}));

const mockChatRepo = vi.hoisted(() => ({
  getByUserId: vi.fn(),
  appendMessages: vi.fn(),
}));

const mockLLMProvider = vi.hoisted(() => ({
  generateChatReply: vi.fn(),
}));

vi.mock("../../lib/repositories/userRepository", () => mockUserRepo);
vi.mock("../../lib/repositories/chatRepository", () => mockChatRepo);
vi.mock("../../lib/llm/llmProvider", () => mockLLMProvider);

describe("handleMessage", () => {
  const mockUser = { userJob: "développeur", userGoal: "productivité" };
  const defaultInput = {
    userId: "test-user",
    message: "J'ai besoin d'aide avec mon organisation",
    context: "personnel" as ChatContext,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUserRepo.getUserById.mockResolvedValue(mockUser);
    mockChatRepo.getByUserId.mockResolvedValue(null);
    mockChatRepo.appendMessages.mockResolvedValue({
      id: "chat-1",
      userId: "test-user",
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    });
    mockLLMProvider.generateChatReply.mockResolvedValue({
      message: "Bonjour ! Comment puis-je t'aider ?",
      suggestion: "NONE",
    });
  });

  it("returns correct shape with NONE suggestion when no tool call", async () => {
    mockLLMProvider.generateChatReply.mockResolvedValue({
      message: "Je peux t'aider à organiser ton temps.",
      suggestion: "NONE",
    });

    const result = await handleMessage(defaultInput);
    expect(result).toEqual({
      message: "Je peux t'aider à organiser ton temps.",
      suggestion: "NONE",
    });
  });

  it("returns BOOKING_INTENT when LLM makes a tool call", async () => {
    mockLLMProvider.generateChatReply.mockResolvedValue({
      message: "Je pense qu'un coach humain serait plus adapté.",
      suggestion: "BOOKING_INTENT",
    });

    const result = await handleMessage(defaultInput);
    expect(result.suggestion).toBe("BOOKING_INTENT");
  });

  it("returns degraded message when LLM is unavailable", async () => {
    mockLLMProvider.generateChatReply.mockResolvedValue({
      message: "Je rencontre un souci technique, réessaie dans un instant.",
      suggestion: "NONE",
    });

    const result = await handleMessage(defaultInput);
    expect(result.message).toBe("Je rencontre un souci technique, réessaie dans un instant.");
    expect(result.suggestion).toBe("NONE");
  });

  it("loads history from DB when not provided", async () => {
    mockLLMProvider.generateChatReply.mockResolvedValue({
      message: "Bonjour !",
      suggestion: "NONE",
    });

    await handleMessage(defaultInput);
    expect(mockChatRepo.getByUserId).toHaveBeenCalledWith("test-user");
  });

  it("persists both user and assistant messages", async () => {
    mockLLMProvider.generateChatReply.mockResolvedValue({
      message: "Réponse test",
      suggestion: "NONE",
    });

    await handleMessage(defaultInput);
    expect(mockChatRepo.appendMessages).toHaveBeenCalledTimes(1);
    const callArgs = mockChatRepo.appendMessages.mock.calls[0];
    expect(callArgs[0]).toBe("test-user");
    expect(callArgs[1]).toHaveLength(2);
    expect(callArgs[1][0].role).toBe("user");
    expect(callArgs[1][1].role).toBe("assistant");
  });

  it("throws error for missing user", async () => {
    mockUserRepo.getUserById.mockRejectedValue(
      new mockUserRepo.UserNotFoundError("nonexistent")
    );

    await expect(handleMessage(defaultInput)).rejects.toThrowError(
      "User not found: nonexistent"
    );
  });
});

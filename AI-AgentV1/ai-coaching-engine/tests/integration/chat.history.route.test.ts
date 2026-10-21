import { describe, it, expect, vi, beforeEach } from "vitest";
import { GET } from "../../app/api/chat/history/route";
import * as chatRepository from "../../lib/repositories/chatRepository";

vi.mock("../../lib/repositories/chatRepository", () => ({
  getByUserId: vi.fn(),
}));

function buildRequest(userId?: string): Request {
  const headers = new Headers();
  if (userId !== undefined) {
    headers.set("x-mock-user-id", userId);
  }
  return new Request("http://localhost:3000/api/chat/history", {
    method: "GET",
    headers,
  });
}

describe("GET /api/chat/history", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 401 when x-mock-user-id is missing", async () => {
    const req = buildRequest(undefined);
    const res = await GET(req);
    expect(res.status).toBe(401);
    const body = await res.json();
    expect(body.error).toBe("Unauthorized");
  });

  it("returns 200 with empty messages array when no chat exists", async () => {
    vi.mocked(chatRepository.getByUserId).mockResolvedValue(null);

    const req = buildRequest("new-user");
    const res = await GET(req);
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.messages).toEqual([]);
  });

  it("returns 200 with existing messages", async () => {
    const mockMessages = [
      {
        role: "user" as const,
        content: "Bonjour",
        context: "personnel" as const,
        createdAt: "2025-01-01T00:00:00.000Z",
      },
      {
        role: "assistant" as const,
        content: "Bonjour !",
        context: "personnel" as const,
        suggestion: "NONE" as const,
        createdAt: "2025-01-01T00:00:01.000Z",
      },
    ];

    vi.mocked(chatRepository.getByUserId).mockResolvedValue({
      id: "chat-1",
      userId: "test-user",
      messages: mockMessages,
      createdAt: new Date("2025-01-01"),
      updatedAt: new Date("2025-01-01"),
    });

    const req = buildRequest("test-user");
    const res = await GET(req);
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.messages).toHaveLength(2);
    expect(body.messages[0].role).toBe("user");
    expect(body.messages[1].role).toBe("assistant");
  });
});

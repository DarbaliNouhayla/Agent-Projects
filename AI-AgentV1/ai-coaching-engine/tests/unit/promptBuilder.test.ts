import { describe, it, expect } from "vitest";
import { buildSystemPrompt } from "../../lib/prompts/promptBuilder";
import { BASE_GUARDRAILS } from "../../lib/prompts/base";
import { PERSONNEL_PROMPT } from "../../lib/prompts/personnel";
import { PROFESSIONNEL_PROMPT } from "../../lib/prompts/professionnel";
import { SANTE_PROMPT } from "../../lib/prompts/sante";

describe("buildSystemPrompt", () => {
  const testCases = [
    { context: "personnel" as const, expectedPrompt: PERSONNEL_PROMPT },
    { context: "professionnel" as const, expectedPrompt: PROFESSIONNEL_PROMPT },
    { context: "sante" as const, expectedPrompt: SANTE_PROMPT },
  ];

  for (const { context, expectedPrompt } of testCases) {
    it(`includes the ${context} context prompt when context is ${context}`, () => {
      const result = buildSystemPrompt("développeur", "productivité", context);
      expect(result).toContain(expectedPrompt);
    });
  }

  it("always includes BASE_GUARDRAILS content regardless of context", () => {
    for (const context of ["personnel", "professionnel", "sante"] as const) {
      const result = buildSystemPrompt("manager", "communication", context);
      expect(result).toContain(BASE_GUARDRAILS);
    }
  });

  it("substitutes the user job into the result", () => {
    const result = buildSystemPrompt("développeur", "productivité", "personnel");
    expect(result).toContain("développeur");
  });

  it("substitutes the user goal into the result", () => {
    const result = buildSystemPrompt("développeur", "productivité", "personnel");
    expect(result).toContain("productivité");
  });

  it("returns a non-empty string for all context types", () => {
    for (const context of ["personnel", "professionnel", "sante"] as const) {
      const result = buildSystemPrompt("test", "test", context);
      expect(result.length).toBeGreaterThan(50);
    }
  });

  it("includes user job and goal after context prompt", () => {
    const result = buildSystemPrompt("chef de projet", "gérer le stress", "professionnel");
    expect(result).toContain("Métier de l'utilisateur : chef de projet");
    expect(result).toContain("Objectif de l'utilisateur : gérer le stress");
  });

  it("is a pure function (same inputs produce same output)", () => {
    const input = { userJob: "a", userGoal: "b", context: "personnel" as const };
    const r1 = buildSystemPrompt(input.userJob, input.userGoal, input.context);
    const r2 = buildSystemPrompt(input.userJob, input.userGoal, input.context);
    expect(r1).toBe(r2);
  });
});

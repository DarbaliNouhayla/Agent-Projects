import { BASE_GUARDRAILS } from "./base";
import { PERSONNEL_PROMPT } from "./personnel";
import { PROFESSIONNEL_PROMPT } from "./professionnel";
import { SANTE_PROMPT } from "./sante";

export type ChatContext = "personnel" | "professionnel" | "sante";

const CONTEXT_PROMPTS: Record<ChatContext, string> = {
  personnel: PERSONNEL_PROMPT,
  professionnel: PROFESSIONNEL_PROMPT,
  sante: SANTE_PROMPT,
};

/** Pure function: assembles the full system prompt from guardrails, context prompt, and user profile. */
export function buildSystemPrompt(userJob: string, userGoal: string, context: ChatContext): string {
  return [
    BASE_GUARDRAILS,
    CONTEXT_PROMPTS[context],
    `Métier de l'utilisateur : ${userJob}`,
    `Objectif de l'utilisateur : ${userGoal}`,
  ].join("\n\n");
}

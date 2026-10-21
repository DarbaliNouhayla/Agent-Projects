export const FLAG_EXPERT_REFERRAL_TOOL = {
  type: "function" as const,
  function: {
    name: "flag_expert_referral",
    description:
      'Call this when the user\'s message indicates they would benefit from connecting with a human expert (coach, therapist, doctor, career advisor) — for example: explicit request for human help, a recurring/serious blocker beyond general coaching scope, or a topic that requires professional judgment the AI should not provide. Do not call this for casual mentions or general small talk.',
    parameters: {
      type: "object",
      properties: {
        reason: {
          type: "string",
          description: "Short explanation of why a human expert is warranted, in French.",
        },
        urgency: {
          type: "string",
          enum: ["low", "medium", "high"],
          description: "How urgent the referral seems based on the conversation.",
        },
      },
      required: ["reason", "urgency"],
    },
  },
};

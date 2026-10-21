import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1).refine(
    (v) => v.startsWith("postgresql://") || v.startsWith("postgres://"),
    { message: "DATABASE_URL must start with postgresql:// or postgres://" }
  ),
  GROQ_API_KEY: z.string().min(1),
  GROQ_MODEL: z.string().min(1).default("llama-3.3-70b-versatile"),
  GROQ_TIMEOUT_MS: z.coerce.number().positive().default(15000),
  GROQ_MAX_RETRIES: z.coerce.number().nonnegative().default(2),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  MOCK_AUTH_ENABLED: z.string().default("true"),
});

function loadEnv() {
  const result = envSchema.safeParse(process.env);
  if (!result.success) {
    const missing = result.error.issues
      .map((i) => `${i.path.join(".")}: ${i.message}`)
      .join("; ");
    throw new Error(`Environment variable validation failed: ${missing}`);
  }
  return result.data;
}

export const env = loadEnv();

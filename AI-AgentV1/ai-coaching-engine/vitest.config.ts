import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: ["tests/**/*.test.ts"],
    env: {
      NODE_ENV: "test",
      DATABASE_URL: "postgresql://user:password@localhost:5432/ai_coaching_dev",
      GROQ_API_KEY: "sk-test-dummy-key-for-validation",
      GROQ_MODEL: "llama-3.3-70b-versatile",
      GROQ_TIMEOUT_MS: "15000",
      GROQ_MAX_RETRIES: "2",
      MOCK_AUTH_ENABLED: "true",
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});

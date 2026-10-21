# AI Coaching Assistant — Chat Engine (Module 2)

Backend API for the AI coaching platform's chat functionality. Part of a 5-module project.

## Tech Stack

- **Runtime**: Next.js 16 (App Router, API routes only — no UI)
- **Language**: TypeScript (strict)
- **Database**: PostgreSQL via Prisma ORM 7
- **LLM**: Groq (`llama-3.3-70b-versatile`)
- **Validation**: Zod
- **Testing**: Vitest

## Prerequisites

- Node.js 20+
- Docker (for local Postgres) — or an external PostgreSQL instance
- Groq API key (free tier: https://console.groq.com)

## Setup

```bash
# 1. Install dependencies
npm install

# 2. Start PostgreSQL (Docker)
docker compose up -d

# 3. Copy and configure environment
cp .env.example .env
# Edit .env: set GROQ_API_KEY, adjust DATABASE_URL if needed

# 4. Run Prisma migration + seed
npx prisma migrate dev --name init
npx prisma db seed

# 5. Verify seed data
npx prisma studio
```

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `GROQ_API_KEY` | — | Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model |
| `MOCK_AUTH_ENABLED` | `true` | Use mock auth (remove when Module 1 is integrated) |

## Running the API

```bash
npm run dev
# Server starts at http://localhost:3000
```

## API Endpoints

### `POST /api/chat`

Send a chat message. Requires `x-mock-user-id` header.

```json
{
  "message": "string (1-2000 chars, required)",
  "selected_context": "personnel | professionnel | sante",
  "chat_history": "[optional] previous messages for context"
}
```

Response: `{ "message": "string", "suggestion": "NONE | BOOKING_INTENT" }`

### `GET /api/chat/history`

Returns full message history for the authenticated user.

Response: `{ "messages": [...] }`

## Testing

```bash
# Run all tests (unit + integration)
npm test

# Run individual suites
npm run test:unit
npm run test:integration
npm run test:guardrails   # real Groq API — requires valid GROQ_API_KEY
```

**Note on guardrail tests**: The guardrail corpus (`tests/guardrails/`) hits the real Groq API and consumes quota. Run them sparingly (e.g., nightly CI, not on every commit). They automatically skip if `GROQ_API_KEY` is absent or set to a dummy value.

## Project Structure

```
app/api/chat/           → POST /api/chat
app/api/chat/history/   → GET /api/chat/history
lib/
  auth/mockAuth.ts      → Stub auth (swap when Module 1 is integrated)
  config/env.ts         → Zod-validated env loader
  llm/                  → Groq client, tool schema, LLM provider
  prompts/              → Base guardrails + 3 context prompts
  repositories/         → Prisma data access
  services/             → Business logic orchestration
  validation/           → Zod schemas for request bodies
prisma/                 → Schema, migrations, seed
tests/                  → Unit, integration, guardrail tests
```

## Integration with Module 1 (Real Auth)

When Module 1 (Auth) is ready, only one change is needed:

1. Replace `lib/auth/mockAuth.ts` — keep the interface `getServerSession(Request) => Promise<Session | null>` identical.
2. Remove `MOCK_AUTH_ENABLED` from env vars.
3. The rest of the codebase (routes, services, repositories) requires zero changes.

No frontend, no UI, no pages are included. This is a backend-only module consumed by a separate frontend team.

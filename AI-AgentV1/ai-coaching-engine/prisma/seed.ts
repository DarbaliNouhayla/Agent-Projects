import { PrismaClient } from "../generated/prisma";
import { PrismaPg } from "@prisma/adapter-pg";
import { Pool } from "pg";

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error("DATABASE_URL environment variable is required");
  process.exit(1);
}

const pool = new Pool({ connectionString });
const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

async function main() {
  const users = [
    {
      id: "seed-user-dev",
      userJob: "développeur",
      userGoal: "améliorer sa productivité et mieux gérer son temps",
    },
    {
      id: "seed-user-manager",
      userJob: "manager",
      userGoal: "améliorer la communication et la cohésion de son équipe",
    },
    {
      id: "seed-user-student",
      userJob: "étudiant",
      userGoal: "gérer le stress et trouver un équilibre entre études et vie personnelle",
    },
  ];

  for (const u of users) {
    await prisma.user.upsert({
      where: { id: u.id },
      update: u,
      create: u,
    });
  }

  console.log("Seeded 3 users successfully.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());

/**
 * Entrypoint de infraestrutura: aplica seed CAP-BASE com Prisma real.
 * Requer `DATABASE_URL` e client gerado (`npm run db:generate`).
 */
import { PrismaClient } from "@prisma/client";
import { CapBaseSeedService } from "./cap-base-seed.service.js";

function requireDatabaseUrl(): void {
  const raw = process.env.DATABASE_URL;
  const url = typeof raw === "string" ? raw.trim() : "";
  if (url.length === 0) {
    console.error(
      "cap-base seed: DATABASE_URL não está definida ou está vazia. Exporte uma URL PostgreSQL válida antes de executar npm run db:seed.",
    );
    process.exit(1);
  }
}

async function main(): Promise<void> {
  requireDatabaseUrl();
  const prisma = new PrismaClient();
  try {
    const service = new CapBaseSeedService(prisma);
    const result = await service.run();
    console.log("cap-base seed concluído.");
    console.log(JSON.stringify(result, null, 2));
  } finally {
    await prisma.$disconnect();
  }
}

main().catch((err: unknown) => {
  console.error("cap-base seed falhou:", err);
  process.exitCode = 1;
});

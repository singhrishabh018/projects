import { db } from "@/db";
import { sources } from "@/db/schema";
import { eq } from "drizzle-orm";
import { checkPipelineAuth } from "@/lib/pipeline-auth";

/** Read by the n8n Discovery workflow's RSS-fan-out step (PRD Section 10, step 2). */
export async function GET(request: Request) {
  if (!checkPipelineAuth(request)) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const rows = await db.select().from(sources).where(eq(sources.active, true));
  return Response.json({ sources: rows });
}

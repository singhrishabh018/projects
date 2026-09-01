import { db } from "@/db";
import { discoveredItems } from "@/db/schema";
import { eq, inArray } from "drizzle-orm";
import { checkPipelineAuth } from "@/lib/pipeline-auth";

/** Discovery workflow lands normalized RSS items here (PRD Section 10, step 2). */
export async function POST(request: Request) {
  if (!checkPipelineAuth(request)) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const body = await request.json();
  const items: Array<{ sourceId: string; title: string; link: string; publishedDate?: string; rawSnippet?: string }> =
    Array.isArray(body) ? body : [body];

  let inserted = 0;
  for (const item of items) {
    if (!item.link || !item.title || !item.sourceId) continue;
    const existing = await db.select().from(discoveredItems).where(eq(discoveredItems.link, item.link));
    if (existing.length > 0) continue;
    await db.insert(discoveredItems).values({
      id: crypto.randomUUID(),
      sourceId: item.sourceId,
      title: item.title,
      link: item.link,
      publishedDate: item.publishedDate ?? null,
      rawSnippet: item.rawSnippet ?? null,
      classificationStatus: "pending",
      discoveredAt: new Date().toISOString(),
    });
    inserted++;
  }
  return Response.json({ inserted, received: items.length });
}

/** Classification and Refresh workflows pull work from here (PRD Section 10, steps 3 & 5). */
export async function GET(request: Request) {
  if (!checkPipelineAuth(request)) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const url = new URL(request.url);
  const statusParam = url.searchParams.get("status") ?? "pending,low-confidence";
  const statuses = statusParam.split(",") as Array<"pending" | "classified" | "low-confidence" | "irrelevant">;

  const rows = await db.select().from(discoveredItems).where(inArray(discoveredItems.classificationStatus, statuses));
  return Response.json({ items: rows });
}

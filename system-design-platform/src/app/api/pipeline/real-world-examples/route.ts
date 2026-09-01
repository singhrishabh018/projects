import { db } from "@/db";
import { realWorldExamples } from "@/db/schema";
import { checkPipelineAuth } from "@/lib/pipeline-auth";
import { eq } from "drizzle-orm";

/**
 * Written to by the n8n Classification workflow (PRD Section 10, step 3) once
 * it has mapped a discovered post to taxonomy topic(s) and extracted
 * structured facts. Never accepts full article prose in a rendered field --
 * only the extractedFacts JSON + a short cachedExcerpt for personal reading
 * (Section 9's local-caching allowance), matching the "writes JSON, never the
 * article body" rule.
 */
export async function POST(request: Request) {
  if (!checkPipelineAuth(request)) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const body = await request.json();
  const { id, topicIds, title, sourceName, sourceType, sourceUrl, extractedFacts, cachedExcerpt, publishedDate } = body;

  if (!id || !Array.isArray(topicIds) || !title || !sourceUrl || !extractedFacts) {
    return Response.json({ error: "Missing required fields" }, { status: 400 });
  }

  const existing = await db.select().from(realWorldExamples).where(eq(realWorldExamples.id, id));
  const record = {
    id,
    topicIds,
    title,
    sourceName: sourceName ?? "Unknown",
    sourceType: sourceType ?? "technical-newsletter",
    sourceUrl,
    extractedFacts,
    cachedExcerpt: cachedExcerpt ?? null,
    publishedDate: publishedDate ?? null,
  };

  if (existing.length > 0) {
    await db.update(realWorldExamples).set(record).where(eq(realWorldExamples.id, id));
  } else {
    await db.insert(realWorldExamples).values(record);
  }

  return Response.json({ ok: true });
}

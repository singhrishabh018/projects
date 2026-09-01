import { db } from "@/db";
import { topics } from "@/db/schema";
import { checkPipelineAuth } from "@/lib/pipeline-auth";

/**
 * Feeds the n8n Classification workflow's LLM prompt (PRD Section 10, step 3)
 * so new topics added in the app are picked up without editing the workflow.
 */
export async function GET(request: Request) {
  if (!checkPipelineAuth(request)) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const rows = await db.select({ id: topics.id, title: topics.title }).from(topics);
  return Response.json({ topics: rows });
}

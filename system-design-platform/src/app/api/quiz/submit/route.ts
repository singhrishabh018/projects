import { db } from "@/db";
import { userProgress } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function POST(request: Request) {
  const { topicId, correctCount, totalCount } = await request.json();
  if (!topicId || typeof correctCount !== "number" || typeof totalCount !== "number") {
    return Response.json({ error: "Invalid payload" }, { status: 400 });
  }

  const score = totalCount > 0 ? Math.round((correctCount / totalCount) * 100) : 0;
  const passed = score >= 70;

  const rows = await db.select().from(userProgress).where(eq(userProgress.topicId, topicId));
  const existing = rows[0];
  if (!existing) {
    return Response.json({ error: "Topic not unlocked yet" }, { status: 400 });
  }

  await db
    .update(userProgress)
    .set({
      quizPassed: passed,
      quizAttempts: existing.quizAttempts + 1,
      quizPassedAt: passed ? new Date().toISOString() : existing.quizPassedAt,
      confidenceScore: score,
    })
    .where(eq(userProgress.topicId, topicId));

  return Response.json({ passed, score });
}

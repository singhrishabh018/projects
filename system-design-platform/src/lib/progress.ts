import { db } from "@/db";
import { topics, userProgress } from "@/db/schema";
import { asc, eq } from "drizzle-orm";

function dateOnly(iso: string) {
  return iso.slice(0, 10);
}

/**
 * One topic unlocks per day (PRD Section 7). A topic unlocks once the quiz for
 * the previous topic has been passed AND at least one calendar day has passed
 * since the previous topic unlocked -- whichever is later. Only ever unlocks
 * one topic per call, matching "one topic unlocked per day."
 */
export async function ensureUnlocks() {
  const allTopics = await db.select().from(topics).orderBy(asc(topics.order));
  const allProgress = await db.select().from(userProgress);
  const progressByTopic = new Map(allProgress.map((p) => [p.topicId, p]));

  if (allTopics.length === 0) return;

  const first = allTopics[0];
  if (!progressByTopic.has(first.id)) {
    await db.insert(userProgress).values({
      id: `up-${first.id}`,
      topicId: first.id,
      unlockedAt: new Date().toISOString(),
      quizPassed: false,
      quizAttempts: 0,
      quizPassedAt: null,
      confidenceScore: null,
    });
    return;
  }

  for (let i = 0; i < allTopics.length - 1; i++) {
    const current = progressByTopic.get(allTopics[i].id);
    const next = allTopics[i + 1];
    if (!current || progressByTopic.has(next.id)) continue;

    const today = dateOnly(new Date().toISOString());
    const eligibleByDay = dateOnly(current.unlockedAt) < today;
    if (current.quizPassed && eligibleByDay) {
      await db.insert(userProgress).values({
        id: `up-${next.id}`,
        topicId: next.id,
        unlockedAt: new Date().toISOString(),
        quizPassed: false,
        quizAttempts: 0,
        quizPassedAt: null,
        confidenceScore: null,
      });
      return; // only one topic unlocks per call/day
    }
    return; // next topic in sequence isn't eligible yet, stop here
  }
}

export async function getTopicProgress(topicId: string) {
  const rows = await db.select().from(userProgress).where(eq(userProgress.topicId, topicId));
  return rows[0] ?? null;
}

export async function getAllProgress() {
  return db.select().from(userProgress);
}

import Link from "next/link";
import { db } from "@/db";
import { topics } from "@/db/schema";
import { asc } from "drizzle-orm";
import { ensureUnlocks, getAllProgress } from "@/lib/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export const dynamic = "force-dynamic";

export default async function Home() {
  await ensureUnlocks();

  const allTopics = await db.select().from(topics).orderBy(asc(topics.order));
  const progress = await getAllProgress();
  const progressByTopic = new Map(progress.map((p) => [p.topicId, p]));

  const today = allTopics.find((t) => {
    const p = progressByTopic.get(t.id);
    return p && !p.quizPassed;
  });
  const activeTopic = today ?? [...allTopics].reverse().find((t) => progressByTopic.has(t.id));

  return (
    <div className="flex flex-col gap-8">
      <section>
        <p className="text-xs font-medium uppercase tracking-widest text-emerald-400">
          Today&apos;s topic
        </p>
        {activeTopic ? (
          <TodayCard topicId={activeTopic.id} title={activeTopic.title} difficulty={activeTopic.difficulty} passed={progressByTopic.get(activeTopic.id)?.quizPassed ?? false} />
        ) : (
          <p className="mt-2 text-white/50">No topics unlocked yet.</p>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-widest text-white/40">
          All topics
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {allTopics.map((t) => {
            const p = progressByTopic.get(t.id);
            const unlocked = !!p;
            return (
              <Card key={t.id} className={!unlocked ? "opacity-40" : undefined}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{t.title}</CardTitle>
                    <Badge variant={t.source === "primer" ? "default" : "blue"}>
                      {t.source === "primer" ? "primer" : "AI/GenAI exception"}
                    </Badge>
                  </div>
                  <CardDescription>Day {t.order} · {t.difficulty}</CardDescription>
                </CardHeader>
                <CardContent className="flex items-center justify-between">
                  <span className="text-xs text-white/40">
                    {p?.quizPassed
                      ? `Quiz passed · ${p.confidenceScore}%`
                      : unlocked
                        ? "Unlocked"
                        : "Locked"}
                  </span>
                  {unlocked ? (
                    <Link href={`/topics/${t.id}`}>
                      <Button size="sm" variant="outline">
                        Open
                      </Button>
                    </Link>
                  ) : null}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function TodayCard({
  topicId,
  title,
  difficulty,
  passed,
}: {
  topicId: string;
  title: string;
  difficulty: string;
  passed: boolean;
}) {
  return (
    <Card className="mt-2 border-emerald-500/30 bg-emerald-500/[0.04]">
      <CardHeader>
        <CardTitle className="text-2xl">{title}</CardTitle>
        <CardDescription className="capitalize">{difficulty}</CardDescription>
      </CardHeader>
      <CardContent>
        <Link href={`/topics/${topicId}`}>
          <Button>{passed ? "Review topic" : "Start topic"}</Button>
        </Link>
      </CardContent>
    </Card>
  );
}

import { db } from "@/db";
import { topics } from "@/db/schema";
import { asc } from "drizzle-orm";
import { getAllProgress } from "@/lib/progress";
import { Card, CardContent } from "@/components/ui/card";

export const dynamic = "force-dynamic";

function heatColor(score: number | null) {
  if (score === null) return "#ffffff12"; // unlocked, not quizzed
  if (score >= 90) return "#10b981";
  if (score >= 70) return "#34d399aa";
  if (score >= 40) return "#f59e0b88";
  return "#ef444488";
}

export default async function ProgressPage() {
  const allTopics = await db.select().from(topics).orderBy(asc(topics.order));
  const progress = await getAllProgress();
  const progressByTopic = new Map(progress.map((p) => [p.topicId, p]));

  const attempted = progress.filter((p) => p.confidenceScore !== null);
  const avgConfidence = attempted.length
    ? Math.round(attempted.reduce((a, p) => a + (p.confidenceScore ?? 0), 0) / attempted.length)
    : null;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Confidence heatmap</h1>
        <p className="text-sm text-white/40">
          Color = quiz confidence per topic, not raw completion percentage. Gray = unlocked but
          not yet quizzed.
        </p>
      </div>

      <Card>
        <CardContent className="flex flex-wrap gap-2 pt-5">
          {allTopics.map((t) => {
            const p = progressByTopic.get(t.id);
            const unlocked = !!p;
            return (
              <div
                key={t.id}
                title={`${t.title}${p?.confidenceScore != null ? ` — ${p.confidenceScore}%` : ""}`}
                className="flex h-16 w-16 flex-col items-center justify-center rounded-lg border border-white/10 text-center text-[10px] leading-tight text-white/70"
                style={{ background: unlocked ? heatColor(p!.confidenceScore) : "#ffffff05" }}
              >
                <span className="line-clamp-2 px-1">{t.title}</span>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <div className="flex items-center gap-4 text-xs text-white/40">
        <LegendSwatch color="#ef444488" label="<40%" />
        <LegendSwatch color="#f59e0b88" label="40-69%" />
        <LegendSwatch color="#34d399aa" label="70-89%" />
        <LegendSwatch color="#10b981" label="90-100%" />
        <LegendSwatch color="#ffffff12" label="not quizzed" />
      </div>

      {avgConfidence !== null && (
        <p className="text-sm text-white/60">
          Average confidence across attempted quizzes: <span className="text-white">{avgConfidence}%</span>
        </p>
      )}
    </div>
  );
}

function LegendSwatch({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="h-3 w-3 rounded" style={{ background: color }} />
      {label}
    </span>
  );
}

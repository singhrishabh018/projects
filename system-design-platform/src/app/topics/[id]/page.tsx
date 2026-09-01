import Link from "next/link";
import { notFound } from "next/navigation";
import { db } from "@/db";
import { topics, realWorldExamples, interviewFormatNotes } from "@/db/schema";
import { eq } from "drizzle-orm";
import { getTopicProgress } from "@/lib/progress";
import { TopicDiagram } from "@/components/topic-diagram";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export const dynamic = "force-dynamic";

export default async function TopicPage(props: PageProps<"/topics/[id]">) {
  const { id } = await props.params;

  const rows = await db.select().from(topics).where(eq(topics.id, id));
  const topic = rows[0];
  if (!topic) notFound();

  const progress = await getTopicProgress(id);
  if (!progress) {
    return (
      <Card className="border-amber-500/30 bg-amber-500/[0.04]">
        <CardHeader>
          <CardTitle>This topic isn&apos;t unlocked yet</CardTitle>
          <CardDescription>Clear the current day&apos;s quiz to move forward.</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/">
            <Button variant="outline">Back to today</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  const allExamples = await db.select().from(realWorldExamples);
  const examples = allExamples.filter((e) => e.topicIds.includes(id));

  const allNotes = await db.select().from(interviewFormatNotes);
  const notes = allNotes.filter((n) => n.topicId === id);

  return (
    <div className="flex flex-col gap-8">
      <section>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold text-white">{topic.title}</h1>
          <Badge variant={topic.source === "primer" ? "default" : "blue"}>
            {topic.source === "primer" ? "primer-sourced" : "curated exception"}
          </Badge>
          <Badge variant="outline" className="capitalize">
            {topic.difficulty}
          </Badge>
        </div>
        {topic.primerSectionUrl ? (
          <a
            href={topic.primerSectionUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-1 inline-block text-sm text-emerald-400 hover:underline"
          >
            Read the primer section →
          </a>
        ) : null}
        {topic.contentNote ? (
          <p className="mt-3 rounded-lg border border-white/10 bg-white/[0.02] p-3 text-xs text-white/50">
            {topic.contentNote}
          </p>
        ) : null}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-widest text-white/40">
          Diagram
        </h2>
        <TopicDiagram diagramKey={topic.conceptDiagramKey} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-widest text-white/40">
          Concept facts
        </h2>
        <Card>
          <CardContent className="pt-5">
            <ul className="flex flex-col gap-2 text-sm text-white/80">
              {topic.conceptFacts.map((f, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-emerald-400">›</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-widest text-white/40">
          Real-world lessons
        </h2>
        <div className="flex flex-col gap-3">
          {examples.map((ex) => (
            <Card key={ex.id}>
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <CardTitle>{ex.title}</CardTitle>
                  <Badge variant="outline">{ex.sourceType}</Badge>
                </div>
                <CardDescription>
                  {ex.sourceName}
                  {ex.publishedDate ? ` · ${ex.publishedDate}` : ""}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <ul className="flex flex-col gap-1 text-sm text-white/70">
                  {ex.extractedFacts.facts.map((f, i) => (
                    <li key={i}>• {f}</li>
                  ))}
                  {ex.extractedFacts.scaleNumbers.map((n, i) => (
                    <li key={`n-${i}`} className="text-emerald-400">
                      ▲ {n}
                    </li>
                  ))}
                </ul>
                {ex.extractedFacts.techNamed.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {ex.extractedFacts.techNamed.map((t) => (
                      <Badge key={t} variant="outline">
                        {t}
                      </Badge>
                    ))}
                  </div>
                )}
                {ex.cachedExcerpt ? (
                  <blockquote className="border-l-2 border-white/15 pl-3 text-xs italic text-white/40">
                    {ex.cachedExcerpt}
                  </blockquote>
                ) : null}
                <a
                  href={ex.sourceUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-emerald-400 hover:underline"
                >
                  Read the original →
                </a>
              </CardContent>
            </Card>
          ))}
          {examples.length === 0 && (
            <p className="text-sm text-white/40">
              No real-world examples classified into this topic yet. The Discovery/Classification
              pipeline (n8n) fills this in over time.
            </p>
          )}
        </div>
      </section>

      {notes.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-widest text-white/40">
            Interview format notes
          </h2>
          <div className="flex flex-col gap-2">
            {notes.map((n) => (
              <Card key={n.id}>
                <CardContent className="flex flex-col gap-1 pt-5">
                  <span className="text-sm font-medium text-white">{n.company}</span>
                  <span className="text-sm text-white/60">{n.formatDescription}</span>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      <section className="border-t border-white/10 pt-6">
        <Link href={`/topics/${topic.id}/quiz`}>
          <Button size="lg">
            {progress.quizPassed ? "Retake quiz" : "Take the quiz to unlock tomorrow's topic"}
          </Button>
        </Link>
      </section>
    </div>
  );
}

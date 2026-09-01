import { notFound } from "next/navigation";
import { db } from "@/db";
import { topics, quizQuestions } from "@/db/schema";
import { eq } from "drizzle-orm";
import { getTopicProgress } from "@/lib/progress";
import { QuizClient } from "./quiz-client";

export const dynamic = "force-dynamic";

export default async function QuizPage(props: PageProps<"/topics/[id]/quiz">) {
  const { id } = await props.params;

  const topicRows = await db.select().from(topics).where(eq(topics.id, id));
  const topic = topicRows[0];
  if (!topic) notFound();

  const progress = await getTopicProgress(id);
  if (!progress) notFound();

  const questions = await db.select().from(quizQuestions).where(eq(quizQuestions.topicId, id));

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-1 text-2xl font-semibold text-white">{topic.title} · Quiz</h1>
      <p className="mb-6 text-sm text-white/40">
        Self-graded, Anki-style: read the question, think it through, reveal the answer, mark
        honestly. Pass ≥70% to unlock tomorrow&apos;s topic.
      </p>
      <QuizClient
        topicId={id}
        questions={questions.map((q) => ({
          id: q.id,
          question: q.question,
          answer: q.answer,
          source: q.source,
          sourceUrl: q.sourceUrl,
        }))}
      />
    </div>
  );
}

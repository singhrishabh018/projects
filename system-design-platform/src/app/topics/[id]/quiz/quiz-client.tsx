"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

type Question = {
  id: string;
  question: string;
  answer: string;
  source: string;
  sourceUrl: string | null;
};

const sourceLabel: Record<string, string> = {
  "primer-anki-deck": "Primer Anki deck",
  "other-cc-licensed-deck": "CC-licensed deck",
  "cached-interview-guide": "Cached interview guide",
  "UNSOURCED-gap": "Sourcing gap — see Section 9",
};

export function QuizClient({ topicId, questions }: { topicId: string; questions: Question[] }) {
  const router = useRouter();
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [results, setResults] = useState<boolean[]>([]);
  const [outcome, setOutcome] = useState<{ passed: boolean; score: number } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const q = questions[index];
  const done = index >= questions.length;

  async function mark(correct: boolean) {
    const next = [...results, correct];
    setResults(next);
    setRevealed(false);
    if (index + 1 >= questions.length) {
      setSubmitting(true);
      const correctCount = next.filter(Boolean).length;
      const res = await fetch("/api/quiz/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topicId, correctCount, totalCount: next.length }),
      });
      const data = await res.json();
      setOutcome(data);
      setSubmitting(false);
    }
    setIndex(index + 1);
  }

  if (questions.length === 0) {
    return <p className="text-white/50">No quiz questions seeded for this topic yet.</p>;
  }

  if (done && outcome) {
    return (
      <Card className={outcome.passed ? "border-emerald-500/40" : "border-red-500/40"}>
        <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
          <p className="text-3xl font-semibold text-white">{outcome.score}%</p>
          <p className={outcome.passed ? "text-emerald-400" : "text-red-400"}>
            {outcome.passed ? "Passed — tomorrow's topic will unlock." : "Not yet — try again."}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push(`/topics/${topicId}`)}>
              Back to topic
            </Button>
            <Button onClick={() => router.push("/")}>Dashboard</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Progress value={(index / questions.length) * 100} />
      <p className="text-xs text-white/30">
        Question {Math.min(index + 1, questions.length)} of {questions.length}
      </p>
      <Card>
        <CardContent className="flex flex-col gap-4 pt-5">
          <div className="flex items-center justify-between gap-2">
            <Badge variant={q.source === "UNSOURCED-gap" ? "amber" : "outline"}>
              {sourceLabel[q.source] ?? q.source}
            </Badge>
          </div>
          <p className="text-lg text-white">{q.question}</p>
          {revealed ? (
            <div className="flex flex-col gap-3 border-t border-white/10 pt-4">
              <p className="text-sm text-white/70">{q.answer}</p>
              {q.sourceUrl && (
                <a href={q.sourceUrl} target="_blank" rel="noreferrer" className="text-xs text-emerald-400 hover:underline">
                  Source →
                </a>
              )}
              <div className="flex gap-2">
                <Button variant="destructive" onClick={() => mark(false)} disabled={submitting}>
                  Missed it
                </Button>
                <Button onClick={() => mark(true)} disabled={submitting}>
                  Got it
                </Button>
              </div>
            </div>
          ) : (
            <Button variant="outline" onClick={() => setRevealed(true)}>
              Reveal answer
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

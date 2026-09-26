import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { api } from "../api/client";
import type { Quiz, QuizResult } from "../types";
import { Button, Card, ErrorText, Spinner } from "./ui";

interface Props {
  lessonId: number;
  quiz: Quiz;
  onContinue?: (result: QuizResult) => void;
  continueLabel?: string;
}

export default function QuizRunner({
  lessonId,
  quiz,
  onContinue,
  continueLabel = "Continue",
}: Props) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (result) resultRef.current?.focus();
  }, [result]);

  const submit = useMutation({
    mutationFn: () =>
      api.submitQuiz(
        lessonId,
        quiz.questions.map((q) => ({
          question_id: q.id,
          response: answers[q.id] ?? "",
        })),
      ),
    onSuccess: setResult,
  });

  if (result) {
    const resultById = new Map(result.results.map((r) => [r.question_id, r]));
    const pct = Math.round(result.score * 100);
    return (
      <div
        ref={resultRef}
        tabIndex={-1}
        className="space-y-4 focus:outline-none"
      >
        <Card className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500">Your score</p>
            <p role="status" aria-live="polite" className="text-3xl font-semibold">
              {pct}%
            </p>
          </div>
          <div className="text-end text-sm text-slate-600">
            {result.concept_mastery.map((cm) => (
              <div key={cm.concept_id}>
                Concept #{cm.concept_id} mastery:{" "}
                <span className="font-medium">{Math.round(cm.score * 100)}%</span>
              </div>
            ))}
          </div>
        </Card>

        {quiz.questions.map((q, i) => {
          const r = resultById.get(q.id);
          return (
            <Card
              key={q.id}
              className={
                r?.correct
                  ? "border-s-4 border-s-emerald-400"
                  : "border-s-4 border-s-red-400"
              }
            >
              <p className="font-medium">
                {i + 1}. {q.prompt}
              </p>
              <p className="mt-2 text-sm text-slate-600">
                Your answer:{" "}
                <span className={r?.correct ? "text-emerald-700" : "text-red-700"}>
                  {answers[q.id] || "(blank)"}
                </span>
              </p>
              {!r?.correct && (
                <p className="mt-1 text-sm text-slate-600">
                  Correct answer:{" "}
                  <span className="font-medium">{r?.correct_answer}</span>
                </p>
              )}
              {r?.explanation && (
                <p className="mt-1 text-sm text-slate-500">{r.explanation}</p>
              )}
            </Card>
          );
        })}

        {onContinue && (
          <Button onClick={() => onContinue(result)}>{continueLabel}</Button>
        )}
      </div>
    );
  }

  const answered = quiz.questions.filter((q) => (answers[q.id] ?? "").trim()).length;

  return (
    <div className="space-y-4">
      {quiz.questions.map((q, i) => (
        <Card key={q.id}>
          <div className="flex items-start justify-between gap-3">
            <p id={`q-${q.id}-prompt`} className="font-medium">
              {i + 1}. {q.prompt}
            </p>
            <span className="shrink-0 text-xs text-slate-400">
              difficulty {q.difficulty}/5
            </span>
          </div>

          {q.type === "mcq" && q.options ? (
            <div
              role="radiogroup"
              aria-labelledby={`q-${q.id}-prompt`}
              className="mt-3 space-y-2"
            >
              {q.options.map((opt) => (
                <label
                  key={opt}
                  className={`flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 text-sm ${
                    answers[q.id] === opt
                      ? "border-indigo-400 bg-indigo-50"
                      : "border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <input
                    type="radio"
                    name={`q-${q.id}`}
                    checked={answers[q.id] === opt}
                    onChange={() =>
                      setAnswers((a) => ({ ...a, [q.id]: opt }))
                    }
                    className="accent-indigo-600"
                  />
                  {opt}
                </label>
              ))}
            </div>
          ) : (
            <textarea
              rows={3}
              value={answers[q.id] ?? ""}
              onChange={(e) =>
                setAnswers((a) => ({ ...a, [q.id]: e.target.value }))
              }
              aria-label={`Answer for question ${i + 1}`}
              placeholder="Type your answer..."
              className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
            />
          )}
        </Card>
      ))}

      <ErrorText>{submit.error ? (submit.error as Error).message : ""}</ErrorText>

      <div className="flex items-center gap-3">
        <Button onClick={() => submit.mutate()} disabled={submit.isPending}>
          {submit.isPending ? "Grading..." : "Submit answers"}
        </Button>
        {submit.isPending && <Spinner />}
        <span className="text-sm text-slate-500">
          {answered}/{quiz.questions.length} answered
        </span>
      </div>
    </div>
  );
}

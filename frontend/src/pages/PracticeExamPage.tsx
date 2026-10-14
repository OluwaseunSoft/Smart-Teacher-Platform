import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

export default function PracticeExamPage() {
  const { examId } = useParams();
  const id = Number(examId);
  const exam = useQuery({
    queryKey: ["practice-exam", id],
    queryFn: () => api.getPracticeExam(id),
    enabled: Number.isInteger(id) && id > 0,
    refetchInterval: (query) =>
      query.state.data?.submitted_at ? false : 5000,
  });
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [now, setNow] = useState(Date.now());
  const automaticSubmitStarted = useRef(false);

  useEffect(() => {
    if (exam.data) setAnswers(exam.data.answers);
  }, [exam.data?.id]);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const save = useMutation({
    mutationFn: (next: Record<number, string>) =>
      api.savePracticeExamAnswers(id, next),
  });
  const submit = useMutation({
    mutationFn: (next: Record<number, string>) =>
      api.submitPracticeExam(id, next),
    onSuccess: (result) => {
      automaticSubmitStarted.current = false;
      exam.refetch();
      setAnswers(result.answers);
    },
  });

  useEffect(() => {
    if (!exam.data || exam.data.submitted_at || Object.keys(answers).length === 0) return;
    const timeout = window.setTimeout(() => save.mutate(answers), 500);
    return () => window.clearTimeout(timeout);
  }, [answers, exam.data?.id, exam.data?.submitted_at]);

  const endAt = exam.data
    ? new Date(exam.data.started_at).getTime() + exam.data.duration_seconds * 1000
    : 0;
  const remaining = Math.max(0, Math.ceil((endAt - now) / 1000));
  useEffect(() => {
    if (
      remaining === 0 &&
      exam.data &&
      !exam.data.submitted_at &&
      !automaticSubmitStarted.current
    ) {
      automaticSubmitStarted.current = true;
      submit.mutate(answers);
    }
  }, [remaining, exam.data?.submitted_at, exam.data?.id]);

  if (exam.isLoading) return <Spinner label="Loading practice exam..." />;
  if (exam.isError) return <ErrorText>{(exam.error as Error).message}</ErrorText>;
  if (!exam.data) return null;

  const completed = exam.data.submitted_at !== null;
  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <header className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">
          {completed ? "Practice exam review" : "Timed practice exam"}
        </h1>
        {!completed && (
          <p
            role="timer"
            aria-live="off"
            className="rounded-lg bg-indigo-50 px-4 py-2 font-mono text-lg font-semibold text-indigo-800"
          >
            {minutes}:{String(seconds).padStart(2, "0")}
          </p>
        )}
      </header>

      {completed ? (
        <>
          <Card><p className="text-2xl font-semibold">Score: {Math.round((exam.data.score ?? 0) * 100)}%</p></Card>
          {exam.data.questions.map((question) => {
            const result = exam.data!.review.find((item) => item.question_id === question.id);
            return (
              <Card key={question.id} className="space-y-2">
                <p className="font-medium">{question.prompt}</p>
                <p className="text-sm">Your answer: {exam.data!.answers[question.id] || "(blank)"}</p>
                <p className="text-sm">Correct answer: {result?.correct_answer}</p>
                <p className="text-sm text-slate-600">{result?.explanation}</p>
              </Card>
            );
          })}
        </>
      ) : (
        <>
          {exam.data.questions.map((question, index) => (
            <Card key={question.id} className="space-y-3">
              <p className="font-medium">{index + 1}. {question.prompt}</p>
              {question.type === "mcq" && question.options ? (
                <div className="space-y-2">
                  {question.options.map((option) => (
                    <label key={option} className="flex items-center gap-2">
                      <input
                        type="radio"
                        name={`exam-${question.id}`}
                        checked={answers[question.id] === option}
                        onChange={() => setAnswers((current) => ({ ...current, [question.id]: option }))}
                      />
                      {option}
                    </label>
                  ))}
                </div>
              ) : (
                <textarea
                  rows={3}
                  aria-label={`Answer question ${index + 1}`}
                  className="w-full rounded border p-2"
                  value={answers[question.id] ?? ""}
                  onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                />
              )}
            </Card>
          ))}
          <ErrorText>{submit.error ? (submit.error as Error).message : save.error ? (save.error as Error).message : ""}</ErrorText>
          <Button disabled={submit.isPending} onClick={() => submit.mutate(answers)}>
            {submit.isPending ? "Submitting..." : "Submit exam"}
          </Button>
        </>
      )}
    </div>
  );
}

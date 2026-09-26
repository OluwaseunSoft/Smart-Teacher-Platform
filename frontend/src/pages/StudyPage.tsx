import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";

import { api } from "../api/client";
import QuizRunner from "../components/QuizRunner";
import { Badge, Button, Card, ErrorText, Spinner } from "../components/ui";
import type { NextAction, Quiz } from "../types";

export default function StudyPage() {
  const { sessionId } = useParams();
  const id = Number(sessionId);

  const [action, setAction] = useState<NextAction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeQuiz, setActiveQuiz] = useState<Quiz | null>(null);

  const session = useQuery({
    queryKey: ["session", id],
    queryFn: () => api.getSession(id),
  });

  const loadNext = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const next = await api.nextStep(id);
      setAction(next);
      setActiveQuiz(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadNext();
  }, [loadNext]);

  const takeQuiz = useMutation({
    mutationFn: (lessonId: number) => api.createQuiz(lessonId),
    onSuccess: setActiveQuiz,
    onError: (e: Error) => setError(e.message),
  });

  if (session.isLoading) return <Spinner label="Loading session..." />;
  if (session.error)
    return <ErrorText>{(session.error as Error).message}</ErrorText>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/library" className="text-sm text-indigo-600 hover:underline">
            ← Library
          </Link>
          <h1 className="mt-1 text-2xl font-semibold">Study session</h1>
        </div>
        {action?.concept && <Badge value={action.concept.difficulty} />}
      </div>

      {loading && <Spinner label="Deciding what you need next..." />}
      <ErrorText>{error}</ErrorText>

      {!loading && action && (
        <>
          <Card className="bg-indigo-50/60">
            <p className="text-sm font-medium text-indigo-900">
              {action.message}
            </p>
            {action.concept && (
              <p className="mt-1 text-sm text-indigo-700">
                Concept: {action.concept.title}
              </p>
            )}
          </Card>

          {activeQuiz && (
            <QuizRunner
              lessonId={activeQuiz.lesson_id}
              quiz={activeQuiz}
              onContinue={() => void loadNext()}
              continueLabel="See what's next"
            />
          )}

          {!activeQuiz && action.quiz && (
            <QuizRunner
              lessonId={action.quiz.lesson_id}
              quiz={action.quiz}
              onContinue={() => void loadNext()}
              continueLabel="See what's next"
            />
          )}

          {!activeQuiz && !action.quiz && action.lesson && (
            <>
              <Card>
                <h2 className="text-lg font-semibold">{action.lesson.title}</h2>
                {action.lesson.objectives.length > 0 && (
                  <ul className="mt-3 list-disc space-y-1 ps-5 text-sm text-slate-700">
                    {action.lesson.objectives.map((o) => (
                      <li key={o}>{o}</li>
                    ))}
                  </ul>
                )}
                <div className="prose-lesson mt-4 max-w-none">
                  <ReactMarkdown>{action.lesson.content}</ReactMarkdown>
                </div>
              </Card>
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => takeQuiz.mutate(action.lesson!.id)}
                  disabled={takeQuiz.isPending}
                >
                  {takeQuiz.isPending ? "Building quiz..." : "I'm ready — quiz me"}
                </Button>
                {action.type !== "advance" && (
                  <Button
                    variant="secondary"
                    onClick={() => void loadNext()}
                    disabled={loading}
                  >
                    Something else
                  </Button>
                )}
              </div>
            </>
          )}

          {!activeQuiz && !action.quiz && !action.lesson && (
            <Card className="space-y-3 text-center">
              <p className="text-lg font-medium">{action.message}</p>
              <Link to="/library">
                <Button>Back to library</Button>
              </Link>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

import { Link, useLocation, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import QuizRunner from "../components/QuizRunner";
import { Button, Card, ErrorText, Spinner } from "../components/ui";
import type { Quiz } from "../types";

export default function QuizPage() {
  const { lessonId } = useParams();
  const id = Number(lessonId);
  const location = useLocation();
  const passedQuiz = (location.state as { quiz?: Quiz } | null)?.quiz;

  const lesson = useQuery({
    queryKey: ["lesson", id],
    queryFn: () => api.getLesson(id),
  });

  const quiz = useQuery({
    queryKey: ["quiz", id],
    queryFn: () => api.getQuiz(id),
    enabled: !passedQuiz,
    retry: false,
  });

  const generate = useMutation({
    mutationFn: () => api.createQuiz(id),
  });

  const activeQuiz = passedQuiz ?? quiz.data ?? generate.data;

  return (
    <div className="space-y-6">
      <div>
        <Link
          to={`/lessons/${id}`}
          className="text-sm text-indigo-600 hover:underline"
        >
          ← Back to lesson
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">Quiz</h1>
      </div>

      {!activeQuiz && (quiz.isLoading || generate.isPending) && (
        <Spinner label="Building your quiz..." />
      )}

      {!activeQuiz && !quiz.isLoading && !generate.isPending && (
        <Card className="space-y-3">
          <p className="text-sm text-slate-600">
            No quiz yet for this lesson.
          </p>
          <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
            Generate quiz
          </Button>
          <ErrorText>{generate.error ? (generate.error as Error).message : ""}</ErrorText>
        </Card>
      )}

      {activeQuiz && (
        <QuizRunner
          lessonId={id}
          quiz={activeQuiz}
          onContinue={() => {
            if (lesson.data) {
              window.location.href = `/materials/${lesson.data.material_id}`;
            } else {
              window.location.href = "/";
            }
          }}
          continueLabel="Back to curriculum"
        />
      )}
    </div>
  );
}

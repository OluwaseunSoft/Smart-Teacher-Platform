import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import MarkdownContent from "../components/MarkdownContent";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

export default function LessonPage() {
  const { lessonId } = useParams();
  const id = Number(lessonId);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [questionFormat, setQuestionFormat] = useState<"single" | "multiple">("single");

  const lesson = useQuery({
    queryKey: ["lesson", id],
    queryFn: () => api.getLesson(id),
  });

  const takeQuiz = useMutation({
    mutationFn: () => api.createQuiz(id, questionFormat),
    onSuccess: (quiz) => navigate(`/lessons/${id}/quiz`, { state: { quiz } }),
  });

  const simpler = useMutation({
    mutationFn: () => api.regenerateLesson(id, true),
    onSuccess: (newLesson) => {
      qc.invalidateQueries({ queryKey: ["lessons"] });
      navigate(`/lessons/${newLesson.id}`);
    },
  });

  if (lesson.isLoading) return <Spinner label="Loading lesson..." />;
  if (lesson.error)
    return <ErrorText>{(lesson.error as Error).message}</ErrorText>;
  if (!lesson.data) return null;

  const l = lesson.data;

  return (
    <div className="space-y-6">
      <div>
        <Link
          to={`/materials/${l.material_id}`}
          className="text-sm text-indigo-600 hover:underline"
        >
          ← Back to material
        </Link>
        <h1 dir="auto" className="mt-1 text-2xl font-semibold">{l.title}</h1>
      </div>

      {l.objectives.length > 0 && (
        <Card>
          <p className="mb-2 text-sm font-semibold text-slate-500">
            Learning objectives
          </p>
          <ul dir="auto" className="list-disc space-y-1 ps-5 text-sm text-slate-700">
            {l.objectives.map((o) => (
              <li dir="auto" key={o}>{o}</li>
            ))}
          </ul>
        </Card>
      )}

      <Card>
        <div dir="auto" className="prose-lesson max-w-none">
          <MarkdownContent>{l.content || "_No content generated._"}</MarkdownContent>
        </div>
      </Card>

      <div className="flex flex-wrap gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="quiz-format" className="text-sm font-medium">
            Optional quiz format
          </label>
          <select
            id="quiz-format"
            value={questionFormat}
            onChange={(event) => setQuestionFormat(event.target.value as "single" | "multiple")}
            className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 text-sm"
          >
            <option value="single">Single-choice questions</option>
            <option value="multiple">Multiple-choice questions</option>
          </select>
          <Button onClick={() => takeQuiz.mutate()} disabled={takeQuiz.isPending}>
            {takeQuiz.isPending ? "Building quiz..." : "Generate optional quiz"}
          </Button>
        </div>
        <Button
          variant="secondary"
          onClick={() => simpler.mutate()}
          disabled={simpler.isPending}
        >
          {simpler.isPending ? "Rewriting..." : "Explain it simpler"}
        </Button>
      </div>

      <ErrorText>{takeQuiz.error ? (takeQuiz.error as Error).message : ""}</ErrorText>
      <ErrorText>{simpler.error ? (simpler.error as Error).message : ""}</ErrorText>
    </div>
  );
}

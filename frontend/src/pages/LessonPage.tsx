import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";

import { api } from "../api/client";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

export default function LessonPage() {
  const { lessonId } = useParams();
  const id = Number(lessonId);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const lesson = useQuery({
    queryKey: ["lesson", id],
    queryFn: () => api.getLesson(id),
  });

  const takeQuiz = useMutation({
    mutationFn: () => api.createQuiz(id),
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
        <h1 className="mt-1 text-2xl font-semibold">{l.title}</h1>
      </div>

      {l.objectives.length > 0 && (
        <Card>
          <p className="mb-2 text-sm font-semibold text-slate-500">
            Learning objectives
          </p>
          <ul className="list-disc space-y-1 ps-5 text-sm text-slate-700">
            {l.objectives.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ul>
        </Card>
      )}

      <Card>
        <div className="prose-lesson max-w-none">
          <ReactMarkdown>{l.content || "_No content generated._"}</ReactMarkdown>
        </div>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Button onClick={() => takeQuiz.mutate()} disabled={takeQuiz.isPending}>
          {takeQuiz.isPending ? "Building quiz..." : "Take the quiz"}
        </Button>
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

import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { Badge, Button, Card, ErrorText, Spinner } from "../components/ui";

export default function MaterialDetailPage() {
  const { materialId } = useParams();
  const id = Number(materialId);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const material = useQuery({
    queryKey: ["material", id],
    queryFn: () => api.getMaterial(id),
    refetchInterval: (query) =>
      query.state.data?.status === "processing" ? 2000 : false,
    enabled: Number.isFinite(id),
  });

  const concepts = useQuery({
    queryKey: ["concepts", id],
    queryFn: () => api.listConcepts(id),
    enabled: material.data?.status === "ready",
  });

  const lessons = useQuery({
    queryKey: ["lessons", id],
    queryFn: () => api.listLessons(id),
    enabled: material.data?.status === "ready",
  });

  const curriculum = useQuery({
    queryKey: ["curriculum", "material", id],
    queryFn: () => api.materialCurriculum(id),
    enabled: material.data?.status === "ready",
  });

  const process = useMutation({
    mutationFn: () => api.processMaterial(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["material", id] });
    },
  });

  const start = useMutation({
    mutationFn: () => api.createSession(id),
    onSuccess: (session) => navigate(`/study/${session.id}`),
  });

  if (material.isLoading) return <Spinner label="Loading material..." />;
  if (material.error)
    return <ErrorText>{(material.error as Error).message}</ErrorText>;
  if (!material.data) return null;

  const m = material.data;
  const lessonByConcept = new Map(
    (lessons.data ?? []).map((l) => [l.concept_id, l]),
  );
  const topicByConcept = new Map(
    (curriculum.data?.subjects ?? []).flatMap((subject) =>
      subject.chapters.flatMap((chapter) =>
        chapter.topics
        .filter(
          (topic): topic is typeof topic & { concept_id: number } =>
            topic.concept_id !== null,
        )
        .map((topic) => [topic.concept_id, topic] as const),
      ),
    ),
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/library" className="text-sm text-indigo-600 hover:underline">
            ← Library
          </Link>
          <h1 className="mt-1 text-2xl font-semibold">{m.title}</h1>
        </div>
        <Badge value={m.status} />
      </div>

      {m.status === "uploaded" && (
        <Card className="flex items-center justify-between">
          <p className="text-sm text-slate-600">
            Ready to read and organize this material into lessons?
          </p>
          <Button onClick={() => process.mutate()} disabled={process.isPending}>
            {process.isPending ? "Processing..." : "Process material"}
          </Button>
        </Card>
      )}

      {m.status === "processing" && (
        <Card>
          <Spinner label="Reading, organizing, and writing lessons..." />
        </Card>
      )}

      {m.status === "failed" && (
        <Card className="space-y-2">
          <ErrorText>{m.error ?? "Processing failed."}</ErrorText>
          <Button variant="secondary" onClick={() => process.mutate()}>
            Retry
          </Button>
        </Card>
      )}

      {m.status === "ready" && (
        <>
          <Card className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-medium">
                {concepts.data?.length ?? 0} concepts
              </p>
              <p className="text-sm text-slate-500">
                Study adaptively — Suhail decides what you need next.
              </p>
            </div>
            <Button onClick={() => start.mutate()} disabled={start.isPending}>
              {start.isPending ? "Starting..." : "Start study session"}
            </Button>
          </Card>
          <ErrorText>
            {start.error ? (start.error as Error).message : ""}
          </ErrorText>
          {(concepts.isError || lessons.isError || curriculum.isError) && (
            <ErrorText>
              {((concepts.error ?? lessons.error ?? curriculum.error) as Error).message}
            </ErrorText>
          )}

          <section className="space-y-3">
            <h2 className="text-lg font-semibold">Curriculum</h2>
            {(concepts.data ?? []).map((c) => {
              const lesson = lessonByConcept.get(c.id);
              const topic = topicByConcept.get(c.id);
              return (
                <Card
                  key={c.id}
                  className={c.parent_id ? "ms-6 border-s-4 border-s-indigo-200" : ""}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-400">
                          {c.order_index + 1}.
                        </span>
                        <h3 className="font-medium">{c.title}</h3>
                        <Badge value={c.difficulty} />
                      </div>
                      <p className="mt-1 text-sm text-slate-600 line-clamp-2">
                        {c.summary}
                      </p>
                    </div>
                    {topic ? (
                      <Link to={`/topics/${topic.id}`}>
                        <Button variant="secondary">Open topic</Button>
                      </Link>
                    ) : lesson ? (
                      <Link to={`/lessons/${lesson.id}`}>
                        <Button variant="secondary">Open lesson</Button>
                      </Link>
                    ) : (
                      <span className="text-xs text-slate-400">No lesson</span>
                    )}
                  </div>
                </Card>
              );
            })}
          </section>
        </>
      )}
    </div>
  );
}

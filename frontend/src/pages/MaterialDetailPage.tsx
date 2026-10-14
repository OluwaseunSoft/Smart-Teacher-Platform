import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { Badge, Button, Card, ErrorText, Spinner } from "../components/ui";

interface ChapterGroup {
  title: string;
  topic_ids: number[];
}

export default function MaterialDetailPage() {
  const { materialId } = useParams();
  const id = Number(materialId);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [editedTitle, setEditedTitle] = useState("");
  const [subjectName, setSubjectName] = useState("");
  const [chapterGroups, setChapterGroups] = useState<ChapterGroup[]>([]);

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
  const practiceExam = useMutation({
    mutationFn: (chapterId: number) => api.createPracticeExam(chapterId, 30),
    onSuccess: (exam) => navigate(`/practice-exams/${exam.id}`),
  });

  const correction = useMutation({
    mutationFn: () =>
      api.correctMaterial(id, {
        title: editedTitle.trim(),
        subject_name: subjectName.trim() || undefined,
        chapters: chapterGroups.length ? chapterGroups : undefined,
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["material", id] });
      void qc.invalidateQueries({ queryKey: ["curriculum", "material", id] });
      void qc.invalidateQueries({ queryKey: ["curriculum"] });
    },
  });

  useEffect(() => {
    const currentMaterial = material.data;
    if (!currentMaterial) return;
    setEditedTitle((current) => current || currentMaterial.title);
    const currentSubjects = curriculum.data?.subjects ?? [];
    if (currentSubjects.length) {
      setSubjectName((current) => current || currentSubjects[0].name);
      setChapterGroups((current) =>
        current.length
          ? current
          : currentSubjects.flatMap((subject) =>
              subject.chapters.map((chapter) => ({
                title: chapter.title,
                topic_ids: chapter.topics.map((topic) => topic.id),
              })),
            ),
      );
    }
  }, [material.data, curriculum.data]);

  if (material.isLoading) return <Spinner label="Loading material..." />;
  if (material.error)
    return <ErrorText>{(material.error as Error).message}</ErrorText>;
  if (!material.data) return null;

  const m = material.data;
  const subjects = curriculum.data?.subjects ?? [];

  function moveTopic(topicId: number, targetIndex: number) {
    setChapterGroups((groups) => {
      const next = groups.map((group) => ({
        ...group,
        topic_ids: group.topic_ids.filter((currentId) => currentId !== topicId),
      }));
      next[targetIndex]?.topic_ids.push(topicId);
      return next;
    });
  }

  function splitTopic(topicId: number) {
    const title = topicById.get(topicId)?.title ?? "New chapter";
    setChapterGroups((groups) => [
      ...groups.map((group) => ({
        ...group,
        topic_ids: group.topic_ids.filter((currentId) => currentId !== topicId),
      })),
      { title, topic_ids: [topicId] },
    ]);
  }
  const lessonByConcept = new Map(
    (lessons.data ?? []).map((l) => [l.concept_id, l]),
  );
  const topicByConcept = new Map(
    subjects.flatMap((subject) =>
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
  const topicById = new Map(
    subjects.flatMap((subject) =>
      subject.chapters.flatMap((chapter) => chapter.topics.map((topic) => [topic.id, topic] as const)),
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
          <Card className="space-y-4">
            <h2 className="text-lg font-semibold">Correct the material filing</h2>
            <label className="block space-y-1 text-sm">
              <span>Material name</span>
              <input className="w-full rounded border px-3 py-2" value={editedTitle} onChange={(event) => setEditedTitle(event.target.value)} />
            </label>
            {subjects.length > 0 && (
              <>
                <label className="block space-y-1 text-sm">
                  <span>Subject folder</span>
                  <input className="w-full rounded border px-3 py-2" value={subjectName} onChange={(event) => setSubjectName(event.target.value)} />
                </label>
                <div className="space-y-3">
                  {chapterGroups.map((group, index) => (
                    <div key={`${index}:${group.title}`} className="rounded-lg border p-3">
                      <label className="block space-y-1 text-sm">
                        <span>Chapter {index + 1}</span>
                        <input className="w-full rounded border px-3 py-2" value={group.title} onChange={(event) => setChapterGroups((all) => all.map((entry, at) => at === index ? { ...entry, title: event.target.value } : entry))} />
                      </label>
                      {group.topic_ids.map((topicId) => (
                        <div key={topicId} className="mt-2 flex flex-wrap items-center gap-2 text-sm">
                          <span className="flex-1">{topicById.get(topicId)?.title}</span>
                          <select aria-label={`Move ${topicById.get(topicId)?.title}`} value={index} onChange={(event) => moveTopic(topicId, Number(event.target.value))} className="rounded border px-2 py-1">
                            {chapterGroups.map((option, optionIndex) => <option key={optionIndex} value={optionIndex}>{option.title}</option>)}
                          </select>
                          <Button type="button" variant="ghost" onClick={() => splitTopic(topicId)}>Split into chapter</Button>
                        </div>
                      ))}
                    </div>
                  ))}
                  <Button type="button" variant="secondary" onClick={() => setChapterGroups((groups) => [...groups, { title: "New chapter", topic_ids: [] }])}>Add chapter</Button>
                </div>
              </>
            )}
            <ErrorText>{correction.error ? correction.error.message : ""}</ErrorText>
            <Button onClick={() => correction.mutate()} disabled={correction.isPending || !editedTitle.trim()}>
              {correction.isPending ? "Saving corrections..." : "Save corrections"}
            </Button>
          </Card>
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
          <Card className="space-y-3">
            <h2 className="text-lg font-semibold">Timed chapter practice exams</h2>
            {subjects.flatMap((subject) =>
              subject.chapters.map((chapter) => (
                <div key={chapter.id} className="flex flex-wrap items-center gap-3">
                  <span className="flex-1">{subject.name} · {chapter.title}</span>
                  <Button
                    variant="secondary"
                    disabled={practiceExam.isPending || chapter.topics.length === 0}
                    onClick={() => practiceExam.mutate(chapter.id)}
                  >
                    Start 30-minute exam
                  </Button>
                </div>
              )),
            )}
            <ErrorText>{practiceExam.error ? practiceExam.error.message : ""}</ErrorText>
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

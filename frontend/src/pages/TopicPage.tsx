import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";

import { api } from "../api/client";
import { Button, Card, ErrorText, Spinner } from "../components/ui";
import type { Lesson } from "../types";

const TABS = [
  { id: "notes", label: "Notes" },
  { id: "flashcards", label: "Flashcards" },
  { id: "quiz", label: "Quiz" },
  { id: "tutor", label: "Tutor" },
  { id: "source", label: "Source" },
] as const;

type TopicTab = (typeof TABS)[number]["id"];

function TopicTutor({ topicId }: { topicId: number }) {
  const queryClient = useQueryClient();
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");

  const conversation = useQuery({
    queryKey: ["tutor", "conversation", conversationId],
    queryFn: () => api.getTutorConversation(conversationId!),
    enabled: conversationId !== null,
  });

  const send = useMutation({
    mutationFn: async (content: string) => {
      let id = conversationId;
      if (id === null) {
        const created = await api.createTutorConversation({ topic_id: topicId });
        id = created.id;
        setConversationId(id);
      }
      return api.sendTutorMessage(id, content);
    },
    onSuccess: () => {
      setDraft("");
      void queryClient.invalidateQueries({
        queryKey: ["tutor", "conversation"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["tutor", "conversations"],
      });
    },
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (content && !send.isPending) send.mutate(content);
  }

  return (
    <Card className="flex min-h-[420px] flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">Ask the tutor</h2>
        <p className="text-sm text-slate-600">
          Questions are attached to this topic and grounded in your study material.
        </p>
      </div>

      <div
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        className="min-h-40 flex-1 space-y-4 overflow-y-auto"
      >
        {conversationId === null && (
          <p className="text-sm text-slate-500">
            Send a question to start a topic-specific conversation.
          </p>
        )}
        {conversation.isLoading && <Spinner label="Loading conversation..." />}
        {conversation.isError && (
          <ErrorText>{(conversation.error as Error).message}</ErrorText>
        )}
        {conversation.data?.messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm ${
                message.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-800"
              }`}
            >
              {message.role === "assistant" ? (
                <>
                  <div className="prose-lesson">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                  {message.grounding.length > 0 && (
                    <p className="mt-2 border-t border-slate-300 pt-2 text-xs text-slate-500">
                      Sources:{" "}
                      {message.grounding
                        .map((reference) => `#${(reference.index ?? 0) + 1}`)
                        .join(", ")}
                    </p>
                  )}
                </>
              ) : (
                <p className="whitespace-pre-wrap">{message.content}</p>
              )}
            </div>
          </div>
        ))}
        {send.isPending && <Spinner label="Tutor is thinking..." />}
      </div>

      <ErrorText>{send.error ? send.error.message : ""}</ErrorText>
      <form onSubmit={submit} className="flex items-end gap-2 border-t border-slate-200 pt-4">
        <label className="sr-only" htmlFor="topic-tutor-message">
          Your question
        </label>
        <textarea
          id="topic-tutor-message"
          rows={2}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask a question about this topic..."
          className="min-w-0 flex-1 resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
        />
        <Button type="submit" disabled={send.isPending || !draft.trim()}>
          Send
        </Button>
      </form>
    </Card>
  );
}

function TopicFlashcards({
  topicId,
  lesson,
  summary,
}: {
  topicId: number;
  lesson: Lesson | null;
  summary: string;
}) {
  const queryClient = useQueryClient();
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [reviewed, setReviewed] = useState(0);

  const cards = lesson?.objectives.length
    ? lesson.objectives.map((objective) => ({
        prompt: "What should you be able to explain?",
        answer: objective,
      }))
    : [
        {
          prompt: `What is ${lesson?.title ?? "this topic"} about?`,
          answer: summary || "Review the topic notes and source material.",
        },
      ];
  const complete = index >= cards.length;

  const rate = useMutation({
    mutationFn: (quality: number) => api.submitReview(topicId, quality),
    onSuccess: () => {
      setReviewed((count) => count + 1);
      setIndex((current) => current + 1);
      setFlipped(false);
      void queryClient.invalidateQueries({ queryKey: ["reviews"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (complete) {
    return (
      <Card className="space-y-4 text-center">
        <h2 className="text-xl font-semibold">Session complete</h2>
        <p className="text-sm text-slate-600">
          You reviewed {reviewed} {reviewed === 1 ? "card" : "cards"}.
        </p>
        <Button
          variant="secondary"
          onClick={() => {
            setIndex(0);
            setReviewed(0);
          }}
        >
          Review again
        </Button>
      </Card>
    );
  }

  const card = cards[index];

  return (
    <div className="space-y-4">
      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-slate-500">
          <span>Card {index + 1} of {cards.length}</span>
          <span aria-live="polite">{flipped ? "Answer" : "Prompt"}</span>
        </div>
        <button
          type="button"
          aria-label={flipped ? "Show flashcard prompt" : "Reveal flashcard answer"}
          onClick={() => setFlipped((value) => !value)}
          className="flex min-h-56 w-full items-center justify-center rounded-xl border border-slate-200 bg-slate-50 p-6 text-center text-lg font-medium text-slate-800 hover:border-indigo-300 focus-visible:outline-indigo-600"
        >
          <span>{flipped ? card.answer : card.prompt}</span>
        </button>
        <div className="flex flex-wrap justify-between gap-2">
          <Button variant="secondary" onClick={() => setFlipped((value) => !value)}>
            {flipped ? "Show prompt" : "Reveal answer"}
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              setIndex((current) => current + 1);
              setFlipped(false);
            }}
          >
            Skip
          </Button>
        </div>
      </Card>
      <div className="space-y-2">
        <p className="text-sm font-medium text-slate-700">
          How well did you recall it? Your rating updates the review schedule.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            disabled={!flipped || rate.isPending}
            onClick={() => rate.mutate(0)}
          >
            Again
          </Button>
          <Button
            variant="secondary"
            disabled={!flipped || rate.isPending}
            onClick={() => rate.mutate(3)}
          >
            Good
          </Button>
          <Button
            variant="secondary"
            disabled={!flipped || rate.isPending}
            onClick={() => rate.mutate(5)}
          >
            Easy
          </Button>
        </div>
        <ErrorText>{rate.error ? rate.error.message : ""}</ErrorText>
      </div>
    </div>
  );
}

export default function TopicPage() {
  const { topicId } = useParams();
  const id = Number(topicId);
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TopicTab>("notes");
  const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);

  const topic = useQuery({
    queryKey: ["topic", id],
    queryFn: () => api.getTopic(id),
    enabled: Number.isInteger(id) && id > 0,
  });
  const selectedLessonExists = topic.data?.lessons.some(
    (topicLesson) => topicLesson.id === selectedLessonId,
  );
  const lessonId =
    (selectedLessonExists ? selectedLessonId : null) ??
    topic.data?.lessons[0]?.id ??
    null;
  const lesson = useQuery({
    queryKey: ["lesson", lessonId],
    queryFn: () => api.getLesson(lessonId!),
    enabled: lessonId !== null,
  });
  const createQuiz = useMutation({
    mutationFn: () => api.createQuiz(lessonId!),
    onSuccess: (quiz) =>
      navigate(`/lessons/${lessonId}/quiz`, { state: { quiz } }),
  });

  if (!Number.isInteger(id) || id < 1) {
    return <ErrorText>Invalid topic.</ErrorText>;
  }
  if (topic.isLoading) return <Spinner label="Loading topic..." />;
  if (topic.isError) return <ErrorText>{(topic.error as Error).message}</ErrorText>;
  if (!topic.data) return null;

  const item = topic.data;
  const activeLesson = lesson.data ?? null;
  const handleTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const currentIndex = TABS.findIndex((tab) => tab.id === activeTab);
    const isRtl = document.documentElement.dir === "rtl";
    let nextIndex = currentIndex;

    if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = TABS.length - 1;
    else if (event.key === "ArrowRight") {
      nextIndex = (currentIndex + (isRtl ? -1 : 1) + TABS.length) % TABS.length;
    } else if (event.key === "ArrowLeft") {
      nextIndex = (currentIndex + (isRtl ? 1 : -1) + TABS.length) % TABS.length;
    } else return;

    event.preventDefault();
    const nextTab = TABS[nextIndex];
    setActiveTab(nextTab.id);
    document.getElementById(`topic-tab-${nextTab.id}`)?.focus();
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header className="space-y-3">
        {item.source_material_id && (
          <Link
            to={`/materials/${item.source_material_id}`}
            className="inline-flex min-h-11 items-center text-sm font-medium text-indigo-600 hover:underline"
          >
            ← Back to {item.source_title || "material"}
          </Link>
        )}
        <div>
          <p className="text-sm font-medium text-indigo-700">Topic {item.order_index + 1}</p>
          <h1 className="mt-1 break-words text-2xl font-semibold sm:text-3xl">{item.title}</h1>
          <p className="mt-2 max-w-3xl text-slate-600">{item.summary}</p>
        </div>
        {item.lessons.length > 1 && (
          <div className="flex flex-wrap gap-2" aria-label="Lessons for this topic">
            {item.lessons.map((topicLesson) => (
              <Button
                key={topicLesson.id}
                type="button"
                variant={
                  lessonId === topicLesson.id ? "primary" : "secondary"
                }
                onClick={() => setSelectedLessonId(topicLesson.id)}
              >
                {topicLesson.title}
              </Button>
            ))}
          </div>
        )}
      </header>

      <div
        role="tablist"
        aria-label={`${item.title} study sections`}
        className="flex gap-1 overflow-x-auto border-b border-slate-200"
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            id={`topic-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            tabIndex={activeTab === tab.id ? 0 : -1}
            aria-controls={`topic-panel-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            onKeyDown={handleTabKeyDown}
            className={`min-h-11 shrink-0 border-b-2 px-3 text-sm font-medium focus-visible:outline-indigo-600 sm:px-4 ${
              activeTab === tab.id
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <section
        id="topic-panel-notes"
        role="tabpanel"
        aria-labelledby="topic-tab-notes"
        tabIndex={0}
        hidden={activeTab !== "notes"}
        className="min-w-0 focus:outline-none"
      >
          <div className="space-y-4">
            {lesson.isLoading && <Spinner label="Loading notes..." />}
            {lesson.isError && (
              <ErrorText>{(lesson.error as Error).message}</ErrorText>
            )}
            {activeLesson ? (
              <>
                {activeLesson.objectives.length > 0 && (
                  <Card>
                    <h2 className="font-semibold">Learning objectives</h2>
                    <ul className="mt-2 list-disc space-y-1 ps-5 text-sm text-slate-700">
                      {activeLesson.objectives.map((objective) => (
                        <li key={objective}>{objective}</li>
                      ))}
                    </ul>
                  </Card>
                )}
                <Card>
                  <h2 className="mb-3 text-lg font-semibold">{activeLesson.title}</h2>
                  <div className="prose-lesson max-w-none break-words">
                    <ReactMarkdown>
                      {activeLesson.content || item.summary || "_No notes available yet._"}
                    </ReactMarkdown>
                  </div>
                </Card>
              </>
            ) : !lesson.isLoading && !lesson.isError ? (
              <Card>
                <h2 className="font-semibold">Topic notes</h2>
                <p className="mt-2 text-sm leading-7 text-slate-700">
                  {item.summary || "No lesson notes are available for this topic yet."}
                </p>
              </Card>
            ) : null}
          </div>
      </section>

      <section
        id="topic-panel-flashcards"
        role="tabpanel"
        aria-labelledby="topic-tab-flashcards"
        tabIndex={0}
        hidden={activeTab !== "flashcards"}
        className="min-w-0 focus:outline-none"
      >
        {lesson.isLoading ? (
          <Spinner label="Preparing flashcards..." />
        ) : lesson.isError ? (
          <ErrorText>{(lesson.error as Error).message}</ErrorText>
        ) : (
          <TopicFlashcards
            key={`${item.id}:${lessonId ?? "topic"}`}
            topicId={item.id}
            lesson={activeLesson}
            summary={item.summary}
          />
        )}
      </section>

      <section
        id="topic-panel-quiz"
        role="tabpanel"
        aria-labelledby="topic-tab-quiz"
        tabIndex={0}
        hidden={activeTab !== "quiz"}
        className="min-w-0 focus:outline-none"
      >
          <Card className="space-y-4">
            <h2 className="text-lg font-semibold">Check your understanding</h2>
            <p className="text-sm text-slate-600">
              Generate a quiz based on this topic's lesson, then answer and review each question.
            </p>
            {lesson.isLoading && <Spinner label="Loading quiz materials..." />}
            {lesson.isError && (
              <ErrorText>{(lesson.error as Error).message}</ErrorText>
            )}
            {!lessonId && !lesson.isLoading && (
              <p className="text-sm text-slate-500">
                A lesson is not available for this topic yet.
              </p>
            )}
            <ErrorText>{createQuiz.error ? createQuiz.error.message : ""}</ErrorText>
            <Button
              disabled={!lessonId || lesson.isLoading || createQuiz.isPending}
              onClick={() => createQuiz.mutate()}
            >
              {createQuiz.isPending ? "Building quiz..." : "Start topic quiz"}
            </Button>
          </Card>
      </section>

      <section
        id="topic-panel-tutor"
        role="tabpanel"
        aria-labelledby="topic-tab-tutor"
        tabIndex={0}
        hidden={activeTab !== "tutor"}
        className="min-w-0 focus:outline-none"
      >
        <TopicTutor key={item.id} topicId={item.id} />
      </section>

      <section
        id="topic-panel-source"
        role="tabpanel"
        aria-labelledby="topic-tab-source"
        tabIndex={0}
        hidden={activeTab !== "source"}
        className="min-w-0 space-y-4 focus:outline-none"
      >
          <div className="space-y-4">
            <Card>
              <h2 className="text-lg font-semibold">Source material</h2>
              <p className="mt-1 text-sm text-slate-600">
                {item.source_title || item.source_filename || "Study material"}
              </p>
              {item.source_filename && (
                <p className="mt-1 break-all text-xs text-slate-500">
                  {item.source_filename}
                </p>
              )}
            </Card>
            {item.grounding.length > 0 ? (
              item.grounding.map((reference) => (
                <Card key={reference.chunk_id} className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-medium">
                      Source excerpt {reference.index + 1}
                    </h3>
                    {reference.relevance !== null && (
                      <span className="text-xs text-slate-500">
                        Relevance {Math.round(reference.relevance * 100)}%
                      </span>
                    )}
                  </div>
                  <p className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-700">
                    {reference.content}
                  </p>
                </Card>
              ))
            ) : (
              <Card>
                <p className="text-sm text-slate-600">
                  No linked source excerpts are available for this topic.
                </p>
              </Card>
            )}
          </div>
      </section>
    </div>
  );
}

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

export default function TutorPage() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [topicId, setTopicId] = useState<number | "">("");
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");

  const curriculum = useQuery({
    queryKey: ["curriculum"],
    queryFn: api.listCurriculum,
  });

  const topics =
    curriculum.data?.flatMap((c) =>
      c.subjects.flatMap((s) => s.chapters.flatMap((ch) => ch.topics)),
    ) ?? [];

  const conversations = useQuery({
    queryKey: ["tutor", "conversations"],
    queryFn: api.listTutorConversations,
  });

  const detail = useQuery({
    queryKey: ["tutor", "conversation", selectedId],
    queryFn: () => api.getTutorConversation(selectedId!),
    enabled: selectedId !== null,
  });

  const create = useMutation({
    mutationFn: () =>
      api.createTutorConversation({
        topic_id: topicId === "" ? null : topicId,
      }),
    onSuccess: (conversation) => {
      setSelectedId(conversation.id);
      setTopicId("");
      qc.invalidateQueries({ queryKey: ["tutor", "conversations"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const send = useMutation({
    mutationFn: (content: string) =>
      api.sendTutorMessage(selectedId!, content),
    onSuccess: () => {
      setDraft("");
      setError("");
      qc.invalidateQueries({
        queryKey: ["tutor", "conversation", selectedId],
      });
      qc.invalidateQueries({ queryKey: ["tutor", "conversations"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.deleteTutorConversation(id),
    onSuccess: (_data, id) => {
      if (selectedId === id) setSelectedId(null);
      qc.invalidateQueries({ queryKey: ["tutor", "conversations"] });
    },
  });

  function submit() {
    const content = draft.trim();
    if (!content || send.isPending) return;
    send.mutate(content);
  }

  return (
    <div className="space-y-6">
      <section className="space-y-1">
        <h1 className="text-2xl font-semibold">{t("tutor.title")}</h1>
        <p className="text-slate-600">{t("tutor.subtitle")}</p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4">
          <Card className="space-y-3">
            <label
              htmlFor="tutor-topic"
              className="block text-sm font-medium text-slate-700"
            >
              {t("tutor.chooseTopic")}
            </label>
            <select
              id="tutor-topic"
              value={topicId}
              onChange={(e) =>
                setTopicId(e.target.value === "" ? "" : Number(e.target.value))
              }
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            >
              <option value="">{t("tutor.general")}</option>
              {topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.title}
                </option>
              ))}
            </select>
            {curriculum.isError && (
              <ErrorText>{(curriculum.error as Error).message}</ErrorText>
            )}
            <Button
              onClick={() => create.mutate()}
              disabled={create.isPending}
              className="w-full"
            >
              {t("tutor.new")}
            </Button>
          </Card>

          <div className="space-y-2">
            {conversations.isLoading && <Spinner />}
            {conversations.isError && (
              <ErrorText>{(conversations.error as Error).message}</ErrorText>
            )}
            {!conversations.isLoading &&
              !conversations.isError &&
              conversations.data?.length === 0 && (
                <p className="text-sm text-slate-500">
                  {t("tutor.noConversations")}
                </p>
              )}
            {conversations.data?.map((c) => (
              <div
                key={c.id}
                className={`flex items-center justify-between rounded-lg border px-3 py-2 text-sm ${
                  selectedId === c.id
                    ? "border-indigo-300 bg-indigo-50"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <button
                  className="min-w-0 flex-1 text-start"
                  onClick={() => setSelectedId(c.id)}
                >
                  <span className="block truncate font-medium text-slate-800">
                    {c.title || c.topic_title || t("tutor.general")}
                  </span>
                  <span className="text-xs text-slate-500">
                    {c.message_count}
                  </span>
                </button>
                <button
                  aria-label={t("tutor.delete")}
                  onClick={() => remove.mutate(c.id)}
                  className="px-1 text-slate-400 hover:text-red-600"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </aside>

        <Card className="flex min-h-[420px] flex-col">
          {selectedId === null ? (
            <p className="m-auto text-sm text-slate-500">{t("tutor.empty")}</p>
          ) : detail.isLoading ? (
            <Spinner label={t("common.loading")} />
          ) : detail.isError ? (
            <ErrorText>{(detail.error as Error).message}</ErrorText>
          ) : (
            <>
              <div
                role="log"
                aria-live="polite"
                aria-relevant="additions"
                className="flex-1 space-y-4 overflow-y-auto pe-1"
              >
                {detail.data?.messages.length === 0 && (
                  <p className="text-sm text-slate-500">{t("tutor.empty")}</p>
                )}
                {detail.data?.messages.map((m) => (
                  <div
                    key={m.id}
                    className={
                      m.role === "user" ? "flex justify-end" : "flex justify-start"
                    }
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${
                        m.role === "user"
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-100 text-slate-800"
                      }`}
                    >
                      {m.role === "assistant" ? (
                        <div className="prose-lesson text-sm">
                          <ReactMarkdown>{m.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{m.content}</p>
                      )}
                    </div>
                  </div>
                ))}
                {send.isPending && <Spinner label={t("tutor.thinking")} />}
              </div>

              <ErrorText>{error}</ErrorText>

              <div className="mt-4 flex items-end gap-2 border-t border-slate-200 pt-4">
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      submit();
                    }
                  }}
                  rows={2}
                  placeholder={t("tutor.placeholder")}
                  aria-label={t("tutor.placeholder")}
                  className="flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                />
                <Button onClick={submit} disabled={send.isPending}>
                  {t("common.send")}
                </Button>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

export default function PlannerPage() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [examDate, setExamDate] = useState("");
  const [subjectId, setSubjectId] = useState<number | "">("");
  const [dailyMinutes, setDailyMinutes] = useState(60);
  const [error, setError] = useState("");

  const curriculum = useQuery({
    queryKey: ["curriculum"],
    queryFn: api.listCurriculum,
  });
  const subjects =
    curriculum.data?.flatMap((c) => c.subjects) ?? [];

  const exams = useQuery({
    queryKey: ["planner", "exams"],
    queryFn: api.listExams,
  });

  const plans = useQuery({
    queryKey: ["planner", "plans"],
    queryFn: api.listPlans,
  });

  const detail = useQuery({
    queryKey: ["planner", "plan", selectedPlanId],
    queryFn: () => api.getPlan(selectedPlanId!),
    enabled: selectedPlanId !== null,
  });

  const createExam = useMutation({
    mutationFn: () =>
      api.createExam({
        title: title.trim(),
        exam_date: examDate,
        subject_id: subjectId === "" ? null : subjectId,
      }),
    onSuccess: () => {
      setTitle("");
      setExamDate("");
      setSubjectId("");
      setError("");
      qc.invalidateQueries({ queryKey: ["planner", "exams"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const deleteExam = useMutation({
    mutationFn: (id: number) => api.deleteExam(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["planner", "exams"] }),
  });

  const generate = useMutation({
    mutationFn: (examId: number) =>
      api.generatePlan({
        exam_date_id: examId,
        daily_minutes: dailyMinutes,
      }),
    onSuccess: (plan) => {
      setSelectedPlanId(plan.id);
      setError("");
      qc.invalidateQueries({ queryKey: ["planner", "plans"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const toggleItem = useMutation({
    mutationFn: ({
      planId,
      itemId,
      status,
    }: {
      planId: number;
      itemId: number;
      status: "pending" | "done";
    }) => api.updatePlanItem(planId, itemId, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["planner", "plan", selectedPlanId] });
      qc.invalidateQueries({ queryKey: ["planner", "plans"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const deletePlan = useMutation({
    mutationFn: (id: number) => api.deletePlan(id),
    onSuccess: (_data, id) => {
      if (selectedPlanId === id) setSelectedPlanId(null);
      qc.invalidateQueries({ queryKey: ["planner", "plans"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  function onAddExam(e: FormEvent) {
    e.preventDefault();
    if (!title.trim() || !examDate) {
      setError(t("common.error"));
      return;
    }
    createExam.mutate();
  }

  return (
    <div className="space-y-8">
      <section className="space-y-1">
        <h1 className="text-2xl font-semibold">{t("planner.title")}</h1>
        <p className="text-slate-600">{t("planner.subtitle")}</p>
      </section>

      <Card className="space-y-4">
        <h2 className="text-lg font-semibold">{t("planner.addExam")}</h2>
        <form onSubmit={onAddExam} className="grid gap-3 sm:grid-cols-2">
          <div>
            <label
              htmlFor="plan-title"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("planner.examTitle")}
            </label>
            <input
              id="plan-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <div>
            <label
              htmlFor="plan-date"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("planner.examDate")}
            </label>
            <input
              id="plan-date"
              type="date"
              value={examDate}
              onChange={(e) => setExamDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <div>
            <label
              htmlFor="plan-subject"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("tutor.chooseTopic")} ({t("common.optional")})
            </label>
            <select
              id="plan-subject"
              value={subjectId}
              onChange={(e) =>
                setSubjectId(e.target.value === "" ? "" : Number(e.target.value))
              }
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            >
              <option value="">—</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            {curriculum.isError && (
              <ErrorText>{(curriculum.error as Error).message}</ErrorText>
            )}
          </div>
          <div>
            <label
              htmlFor="plan-daily"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("planner.dailyMinutes")}
            </label>
            <input
              id="plan-daily"
              type="number"
              min={15}
              max={480}
              value={dailyMinutes}
              onChange={(e) => setDailyMinutes(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <div className="sm:col-span-2">
            <ErrorText>{error}</ErrorText>
            <Button
              type="submit"
              disabled={createExam.isPending}
              className="mt-2"
            >
              {t("planner.addExam")}
            </Button>
          </div>
        </form>
      </Card>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("planner.exams")}</h2>
        {exams.isLoading && <Spinner />}
        {exams.isError && (
          <ErrorText>{(exams.error as Error).message}</ErrorText>
        )}
        {!exams.isLoading && !exams.isError && exams.data?.length === 0 && (
          <p className="text-sm text-slate-500">{t("planner.noExams")}</p>
        )}
        <div className="space-y-2">
          {exams.data?.map((exam) => (
            <Card
              key={exam.id}
              className="flex flex-wrap items-center justify-between gap-3"
            >
              <div>
                <p className="font-medium text-slate-800">{exam.title}</p>
                <p className="text-xs text-slate-500">{exam.exam_date}</p>
              </div>
              <div className="flex gap-2">
                <Button
                  disabled={generate.isPending}
                  onClick={() => generate.mutate(exam.id)}
                >
                  {t("planner.generate")}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => deleteExam.mutate(exam.id)}
                >
                  {t("common.delete")}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("planner.plans")}</h2>
        {plans.isError && (
          <ErrorText>{(plans.error as Error).message}</ErrorText>
        )}
        {!plans.isError && plans.data?.length === 0 && (
          <p className="text-sm text-slate-500">{t("planner.noPlans")}</p>
        )}
        <div className="grid gap-3 sm:grid-cols-2">
          {plans.data?.map((plan) => (
            <Card
              key={plan.id}
              className={`space-y-2 ${
                selectedPlanId === plan.id ? "border-indigo-300" : ""
              }`}
            >
              <button
                className="w-full text-start"
                onClick={() => setSelectedPlanId(plan.id)}
              >
                <p className="font-medium text-slate-800">
                  {plan.exam_title || `#${plan.id}`}
                </p>
                <p className="text-xs text-slate-500">
                  {t("planner.progress", {
                    done: plan.completed_items,
                    total: plan.total_items,
                  })}
                </p>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-indigo-600"
                    style={{ width: `${Math.min(100, plan.percent_complete)}%` }}
                  />
                </div>
              </button>
              <Button
                variant="ghost"
                onClick={() => deletePlan.mutate(plan.id)}
              >
                {t("common.delete")}
              </Button>
            </Card>
          ))}
        </div>
      </section>

      {selectedPlanId !== null && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">{t("planner.items")}</h2>
          {detail.isLoading && <Spinner />}
          {detail.isError && (
            <ErrorText>{(detail.error as Error).message}</ErrorText>
          )}
          <div className="space-y-2">
            {detail.data?.items.map((item) => (
              <Card
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-3"
              >
                <div className="min-w-0">
                  <p
                    className={`font-medium ${
                      item.status === "done"
                        ? "text-slate-400 line-through"
                        : "text-slate-800"
                    }`}
                  >
                    {item.topic_title || `#${item.topic_id}`}
                  </p>
                  <p className="text-xs text-slate-500">
                    {t("planner.minutes", { n: item.estimated_minutes })}
                    {item.scheduled_for
                      ? ` · ${t("planner.scheduled", {
                          date: item.scheduled_for,
                        })}`
                      : ""}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  disabled={toggleItem.isPending}
                  onClick={() =>
                    toggleItem.mutate({
                      planId: selectedPlanId,
                      itemId: item.id,
                      status: item.status === "done" ? "pending" : "done",
                    })
                  }
                >
                  {item.status === "done"
                    ? t("planner.markPending")
                    : t("planner.markDone")}
                </Button>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

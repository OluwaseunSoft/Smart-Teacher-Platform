import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n } from "../i18n";
import { Card, ErrorText, Spinner } from "../components/ui";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card className="group relative overflow-hidden border-slate-200/80 p-5 transition hover:-translate-y-0.5 hover:shadow-md">
      <span aria-hidden="true" className="absolute -end-3 -top-5 h-20 w-20 rounded-full bg-indigo-50 transition group-hover:scale-110" />
      <div className="relative">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">{value}</p>
      </div>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { t } = useI18n();

  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.getDashboard,
  });
  const today = useQuery({
    queryKey: ["study-today"],
    queryFn: api.getStudyToday,
  });

  if (dashboard.isLoading) return <Spinner label={t("common.loading")} />;
  if (dashboard.isError)
    return <ErrorText>{(dashboard.error as Error).message}</ErrorText>;

  const d = dashboard.data!;
  const plan = d.active_plan;

  return (
    <div className="space-y-7">
      <section className="relative isolate overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-700 via-indigo-600 to-violet-600 px-6 py-7 text-white shadow-xl shadow-indigo-200/70 sm:px-8 sm:py-9">
        <div aria-hidden="true" className="absolute -end-8 -top-20 -z-10 h-64 w-64 rounded-full border-[35px] border-white/10" />
        <div aria-hidden="true" className="absolute -bottom-32 end-1/3 -z-10 h-64 w-64 rounded-full bg-violet-400/20 blur-3xl" />
        <div className="max-w-2xl">
          <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-indigo-200">
            {t("dashboard.title")}
          </p>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            {t("dashboard.welcome", { name: user?.display_name ?? "" })}
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-indigo-100 sm:text-base">
            {t("dashboard.subtitle")}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/library"
              className="inline-flex min-h-11 items-center rounded-xl bg-white px-4 text-sm font-bold text-indigo-700 shadow-sm transition hover:bg-indigo-50"
            >
              {t("dashboard.explore")} <span aria-hidden="true" className="ms-2">→</span>
            </Link>
            <Link
              to="/reviews"
              className="inline-flex min-h-11 items-center rounded-xl border border-white/30 bg-white/10 px-4 text-sm font-semibold text-white transition hover:bg-white/20"
            >
              {t("dashboard.startReview")}
            </Link>
          </div>
        </div>
      </section>

      <section aria-label={t("dashboard.title")} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat
          label={t("dashboard.streak")}
          value={`${d.streak.current} · ${t("dashboard.longest", {
            n: d.streak.longest,
          })}`}
        />
        <Stat
          label={t("dashboard.topics")}
          value={`${d.topics_covered} / ${d.topics_total}`}
        />
        <Stat
          label={t("dashboard.mastery")}
          value={`${Math.round(d.average_mastery * 100)}%`}
        />
        <Stat label={t("dashboard.due")} value={String(d.due_reviews)} />
        <Stat label="Study time" value={`${d.study_minutes} min`} />
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold">Study today</h2>
          {today.isLoading && <Spinner />}
          {today.isError && <ErrorText>{(today.error as Error).message}</ErrorText>}
          {!today.isLoading && today.data?.items.length === 0 && (
            <p className="text-sm text-slate-500">No due reviews or missed topics today.</p>
          )}
          {today.data?.items.map((item) => (
            <Link
              key={item.topic_id}
              to={`/topics/${item.topic_id}`}
              className="flex items-center justify-between gap-3 rounded-lg border p-3 hover:border-indigo-300"
            >
              <span className="font-medium">{item.title}</span>
              <span className="text-xs text-slate-500">{item.reason}</span>
            </Link>
          ))}
        </Card>
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold">Upcoming exams</h2>
          {d.upcoming_exams.length === 0 ? (
            <p className="text-sm text-slate-500">No upcoming exams scheduled.</p>
          ) : d.upcoming_exams.map((exam) => (
            <div key={exam.id} className="flex justify-between gap-3 border-b pb-2 text-sm">
              <span>{exam.title}</span>
              <time dateTime={exam.exam_date}>{exam.exam_date}</time>
            </div>
          ))}
        </Card>
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold">Subject progress</h2>
          {d.subject_progress.map((subject) => (
            <div key={subject.subject} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>{subject.subject}</span>
                <span>{subject.covered}/{subject.total} topics · {Math.round(subject.mastery * 100)}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded bg-slate-100">
                <div className="h-full bg-indigo-600" style={{ width: `${Math.round(subject.mastery * 100)}%` }} />
              </div>
            </div>
          ))}
        </Card>
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold">Quiz score trend</h2>
          {d.score_trend.length === 0 ? (
            <p className="text-sm text-slate-500">Complete quizzes to see your score trend.</p>
          ) : d.score_trend.map((point) => (
            <div key={point.date} className="flex justify-between border-b pb-2 text-sm">
              <time dateTime={point.date}>{point.date}</time>
              <span>{Math.round(point.score * 100)}% · {point.attempts} answers</span>
            </div>
          ))}
        </Card>
      </section>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(260px,0.9fr)]">
        <Card className="space-y-5 border-slate-200/80 p-5 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-indigo-600">
                {t("dashboard.plan")}
              </p>
              <h2 className="mt-1 text-lg font-bold text-slate-900">
                {plan ? t("dashboard.plan") : t("dashboard.noPlan")}
              </h2>
            </div>
            <Link
              to="/planner"
              className="inline-flex min-h-10 items-center rounded-lg border border-slate-200 px-3 text-xs font-semibold text-indigo-700 transition hover:border-indigo-200 hover:bg-indigo-50"
            >
              {t("dashboard.makePlan")}
            </Link>
          </div>
          {plan ? (
            <div>
              <div className="mb-2 flex items-end justify-between gap-3">
                <p className="text-sm text-slate-600">
                  {t("dashboard.planProgress", {
                    done: plan.completed_items,
                    total: plan.total_items,
                    percent: Math.round(plan.percent_complete),
                  })}
                </p>
                <span className="text-2xl font-bold text-indigo-700">
                  {Math.round(plan.percent_complete)}%
                </span>
              </div>
              <div
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(plan.percent_complete)}
                aria-label={t("dashboard.plan")}
                className="h-3 overflow-hidden rounded-full bg-indigo-50"
              >
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-600 to-violet-500 transition-[width]"
                  style={{ width: `${Math.min(100, Math.max(0, plan.percent_complete))}%` }}
                />
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5">
              <p className="text-sm text-slate-600">{t("dashboard.noPlan")}</p>
              <Link to="/planner" className="mt-2 inline-flex text-sm font-semibold text-indigo-700 hover:underline">
                {t("dashboard.makePlan")} <span aria-hidden="true" className="ms-1">→</span>
              </Link>
            </div>
          )}
        </Card>

        <Card className="border-slate-200/80 p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                {t("dashboard.mastery")}
              </p>
              <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
                {Math.round(d.average_mastery * 100)}%
              </p>
            </div>
            <span aria-hidden="true" className="grid h-12 w-12 place-items-center rounded-2xl bg-emerald-50 text-xl text-emerald-600">✦</span>
          </div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400"
              style={{ width: `${Math.min(100, Math.max(0, d.average_mastery * 100))}%` }}
            />
          </div>
          <p className="mt-3 text-xs leading-relaxed text-slate-500">
            {t("dashboard.topics")}: {d.topics_covered} / {d.topics_total}
          </p>
        </Card>
      </div>

      <section>
        <div className="mb-3">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-indigo-600">
            {t("nav.workspace")}
          </p>
          <h2 className="mt-1 text-lg font-bold text-slate-900">{t("dashboard.title")}</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Link to="/library" className="group block">
            <Card className="h-full border-slate-200/80 p-5 transition group-hover:-translate-y-0.5 group-hover:border-indigo-200 group-hover:shadow-md">
              <span aria-hidden="true" className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-50 text-lg text-indigo-700">▤</span>
              <p className="mt-4 font-bold text-slate-900 group-hover:text-indigo-700">
                {t("dashboard.explore")}
              </p>
              <p className="mt-1 text-sm leading-relaxed text-slate-500">{t("nav.library")}</p>
            </Card>
          </Link>
          <Link to="/reviews" className="block">
            <Card className="h-full border-slate-200/80 p-5 transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md">
              <span aria-hidden="true" className="grid h-10 w-10 place-items-center rounded-xl bg-amber-50 text-lg text-amber-700">↻</span>
              <p className="mt-4 font-bold text-slate-900">{t("dashboard.startReview")}</p>
              <p className="mt-1 text-sm text-slate-500">{t("dashboard.due")}: {d.due_reviews}</p>
            </Card>
          </Link>
          <Link to="/tutor" className="block">
            <Card className="h-full border-slate-200/80 p-5 transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md">
              <span aria-hidden="true" className="grid h-10 w-10 place-items-center rounded-xl bg-violet-50 text-lg text-violet-700">✦</span>
              <p className="mt-4 font-bold text-slate-900">{t("dashboard.askTutor")}</p>
              <p className="mt-1 text-sm text-slate-500">{t("tutor.subtitle")}</p>
            </Card>
          </Link>
          <Link to="/planner" className="block">
            <Card className="h-full border-slate-200/80 p-5 transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md">
              <span aria-hidden="true" className="grid h-10 w-10 place-items-center rounded-xl bg-sky-50 text-lg text-sky-700">▦</span>
              <p className="mt-4 font-bold text-slate-900">{t("dashboard.makePlan")}</p>
              <p className="mt-1 text-sm text-slate-500">{t("nav.planner")}</p>
            </Card>
          </Link>
          <Link to="/progress" className="block">
            <Card className="h-full border-slate-200/80 p-5 transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md">
              <span aria-hidden="true" className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-lg text-emerald-700">↗</span>
              <p className="mt-4 font-bold text-slate-900">{t("dashboard.achievements")}</p>
              <p className="mt-1 text-sm text-slate-500">
                {d.achievements_unlocked} / {d.achievements_total}
              </p>
            </Card>
          </Link>
        </div>
      </section>
    </div>
  );
}

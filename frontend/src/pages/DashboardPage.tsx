import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n } from "../i18n";
import { Card, ErrorText, Spinner } from "../components/ui";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
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

  if (dashboard.isLoading) return <Spinner label={t("common.loading")} />;
  if (dashboard.isError)
    return <ErrorText>{(dashboard.error as Error).message}</ErrorText>;

  const d = dashboard.data!;
  const plan = d.active_plan;

  return (
    <div className="space-y-8">
      <section className="space-y-1">
        <h1 className="text-2xl font-semibold">
          {t("dashboard.welcome", { name: user?.display_name ?? "" })}
        </h1>
        <p className="text-slate-600">{t("dashboard.subtitle")}</p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
      </div>

      <Card className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{t("dashboard.plan")}</h2>
          <Link
            to="/planner"
            className="text-sm font-medium text-indigo-600 hover:underline"
          >
            {t("dashboard.makePlan")}
          </Link>
        </div>
        {plan ? (
          <div className="space-y-2">
            <p className="text-sm text-slate-600">
              {t("dashboard.planProgress", {
                done: plan.completed_items,
                total: plan.total_items,
                percent: Math.round(plan.percent_complete),
              })}
            </p>
            <div
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(plan.percent_complete)}
              aria-label={t("dashboard.plan")}
              className="h-2 overflow-hidden rounded-full bg-slate-100"
            >
              <div
                className="h-full rounded-full bg-indigo-600"
                style={{ width: `${Math.min(100, plan.percent_complete)}%` }}
              />
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-500">{t("dashboard.noPlan")}</p>
        )}
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link to="/reviews" className="block">
          <Card className="h-full transition hover:border-indigo-300">
            <p className="font-medium text-indigo-700">
              {t("dashboard.startReview")}
            </p>
            <p className="mt-1 text-sm text-slate-500">{t("dashboard.due")}</p>
          </Card>
        </Link>
        <Link to="/tutor" className="block">
          <Card className="h-full transition hover:border-indigo-300">
            <p className="font-medium text-indigo-700">
              {t("dashboard.askTutor")}
            </p>
            <p className="mt-1 text-sm text-slate-500">{t("tutor.subtitle")}</p>
          </Card>
        </Link>
        <Link to="/progress" className="block">
          <Card className="h-full transition hover:border-indigo-300">
            <p className="font-medium text-indigo-700">
              {t("dashboard.achievements")}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              {d.achievements_unlocked} / {d.achievements_total}
            </p>
          </Card>
        </Link>
      </div>
    </div>
  );
}

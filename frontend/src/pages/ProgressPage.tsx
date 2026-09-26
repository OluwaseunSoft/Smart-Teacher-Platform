import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import { Card, ErrorText, Spinner } from "../components/ui";

export default function ProgressPage() {
  const { t, lang } = useI18n();

  const mastery = useQuery({
    queryKey: ["mastery"],
    queryFn: api.listMastery,
  });

  const achievements = useQuery({
    queryKey: ["achievements"],
    queryFn: api.getAchievements,
  });

  const locale = lang === "ar" ? "ar" : "en";

  return (
    <div className="space-y-8">
      <section className="space-y-1">
        <h1 className="text-2xl font-semibold">{t("progress.title")}</h1>
        <p className="text-slate-600">{t("progress.subtitle")}</p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("progress.mastery")}</h2>
        {mastery.isLoading && <Spinner label={t("common.loading")} />}
        {mastery.isError && (
          <ErrorText>{(mastery.error as Error).message}</ErrorText>
        )}
        {!mastery.isLoading && !mastery.isError && mastery.data?.length === 0 && (
          <p className="text-sm text-slate-500">{t("progress.noMastery")}</p>
        )}
        <div className="space-y-2">
          {mastery.data?.map((topic) => (
            <Card key={topic.topic_id} className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="font-medium text-slate-800">{topic.title}</p>
                <span className="text-sm text-slate-500">
                  {Math.round(topic.mastery * 100)}%
                </span>
              </div>
              <div
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(topic.mastery * 100)}
                aria-label={`${topic.title} ${t("progress.mastery")}`}
                className="h-2 overflow-hidden rounded-full bg-slate-100"
              >
                <div
                  className="h-full rounded-full bg-indigo-600"
                  style={{ width: `${Math.min(100, topic.mastery * 100)}%` }}
                />
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">{t("progress.achievements")}</h2>
        {achievements.isLoading && <Spinner />}
        {achievements.isError && (
          <ErrorText>{(achievements.error as Error).message}</ErrorText>
        )}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {achievements.data?.map((a) => (
            <Card
              key={a.code}
              className={`space-y-1 ${a.unlocked ? "" : "opacity-60"}`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xl" aria-hidden="true">
                  {a.unlocked ? a.icon : "🔒"}
                </span>
                <p className="font-medium text-slate-800">{a.name}</p>
              </div>
              <p className="text-sm text-slate-500">{a.description}</p>
              <p className="text-xs text-slate-400">
                {a.unlocked && a.unlocked_at
                  ? t("progress.unlocked", {
                      date: new Date(a.unlocked_at).toLocaleDateString(locale),
                    })
                  : t("progress.locked")}
              </p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}

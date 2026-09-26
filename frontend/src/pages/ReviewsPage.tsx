import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

const QUALITIES = [0, 1, 2, 3, 4, 5];

export default function ReviewsPage() {
  const { t } = useI18n();
  const qc = useQueryClient();

  const summary = useQuery({
    queryKey: ["reviews", "summary"],
    queryFn: api.reviewSummary,
  });

  const queue = useQuery({
    queryKey: ["reviews", "queue"],
    queryFn: () => api.reviewQueue(20),
  });

  const submit = useMutation({
    mutationFn: ({ topicId, quality }: { topicId: number; quality: number }) =>
      api.submitReview(topicId, quality),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reviews"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  return (
    <div className="space-y-8">
      <section className="space-y-1">
        <h1 className="text-2xl font-semibold">{t("reviews.title")}</h1>
        <p className="text-slate-600">{t("reviews.subtitle")}</p>
      </section>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-slate-500">{t("reviews.due")}</p>
          <p className="mt-1 text-2xl font-semibold">
            {summary.data?.due_count ?? 0}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">{t("reviews.scheduled")}</p>
          <p className="mt-1 text-2xl font-semibold">
            {summary.data?.scheduled_count ?? 0}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">{t("reviews.reviewed")}</p>
          <p className="mt-1 text-2xl font-semibold">
            {summary.data?.reviewed_count ?? 0}
          </p>
        </Card>
      </div>

      {queue.isLoading && <Spinner label={t("common.loading")} />}
      {queue.isError && <ErrorText>{(queue.error as Error).message}</ErrorText>}

      {queue.data && queue.data.items.length === 0 && (
        <Card>
          <p className="text-sm text-slate-500">{t("reviews.queueEmpty")}</p>
        </Card>
      )}

      <div className="space-y-4">
        {queue.data?.items.map((item) => (
          <Card key={item.topic_id} className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-medium text-slate-800">{item.topic_title}</h2>
              <div className="text-xs text-slate-500">
                <span>
                  {t("reviews.mastery", {
                    n: Math.round(item.mastery * 100),
                  })}
                </span>
                <span className="mx-2">·</span>
                <span>{t("reviews.interval", { n: item.interval_days })}</span>
              </div>
            </div>

            <p className="text-sm text-slate-600">{t("reviews.howWell")}</p>
            <div
              role="group"
              aria-label={t("reviews.howWell")}
              className="flex flex-wrap gap-2"
            >
              {QUALITIES.map((q) => (
                <Button
                  key={q}
                  variant="secondary"
                  disabled={submit.isPending}
                  onClick={() =>
                    submit.mutate({ topicId: item.topic_id, quality: q })
                  }
                >
                  {t(`reviews.quality.${q}`)}
                </Button>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

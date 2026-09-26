import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

export default function NotificationsPage() {
  const { t, lang } = useI18n();
  const qc = useQueryClient();

  const notifications = useQuery({
    queryKey: ["notifications", "all"],
    queryFn: () => api.listNotifications(false, 50),
  });

  const markAll = useMutation({
    mutationFn: api.markAllNotificationsRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markOne = useMutation({
    mutationFn: (id: number) => api.markNotificationRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const locale = lang === "ar" ? "ar" : "en";
  const unread = notifications.data?.unread ?? 0;

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">{t("notifications.title")}</h1>
          <p className="text-slate-600">{t("notifications.subtitle")}</p>
          {unread > 0 && (
            <p className="text-sm text-indigo-600">
              {t("notifications.unread", { n: unread })}
            </p>
          )}
        </div>
        <Button
          variant="secondary"
          disabled={markAll.isPending || unread === 0}
          onClick={() => markAll.mutate()}
        >
          {t("notifications.markAll")}
        </Button>
      </section>

      {notifications.isLoading && <Spinner label={t("common.loading")} />}
      {notifications.isError && (
        <ErrorText>{(notifications.error as Error).message}</ErrorText>
      )}
      {!notifications.isLoading &&
        !notifications.isError &&
        notifications.data?.items.length === 0 && (
          <Card>
            <p className="text-sm text-slate-500">{t("notifications.empty")}</p>
          </Card>
        )}

      <div className="space-y-2">
        {notifications.data?.items.map((n) => (
          <Card
            key={n.id}
            className={`space-y-1 ${
              n.read_at ? "bg-white" : "border-indigo-200 bg-indigo-50/50"
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium text-slate-800">{n.title}</p>
              <span className="text-xs text-slate-400">
                {new Date(n.created_at).toLocaleString(locale)}
              </span>
            </div>
            <p className="text-sm text-slate-600">{n.body}</p>
            {!n.read_at && (
              <button
                onClick={() => markOne.mutate(n.id)}
                aria-label={`${t("notifications.markRead")}: ${n.title}`}
                className="text-xs font-medium text-indigo-600 hover:underline"
              >
                {t("notifications.markRead")}
              </button>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}

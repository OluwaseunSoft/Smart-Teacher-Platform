import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n } from "../i18n";
import type { User } from "../types";
import { Badge, Button, Card, ErrorText, Spinner } from "../components/ui";

type Tab = "users" | "ai" | "audit";

const PAGE_SIZE = 20;

export default function AdminPage() {
  const { user } = useAuth();
  const { t, lang } = useI18n();
  const [tab, setTab] = useState<Tab>("users");

  const locale = lang === "ar" ? "ar" : "en";

  if (user?.role !== "admin") {
    return (
      <Card>
        <p className="text-sm text-slate-600">{t("admin.forbidden")}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <section className="space-y-1">
        <h1 className="text-2xl font-semibold">{t("admin.title")}</h1>
        <p className="text-slate-600">{t("admin.subtitle")}</p>
      </section>

      <div
        role="tablist"
        aria-label={t("admin.title")}
        className="flex flex-wrap gap-1 border-b border-slate-200"
      >
        {(["users", "ai", "audit"] as const).map((value) => (
          <button
            key={value}
            id={`tab-${value}`}
            role="tab"
            aria-selected={tab === value}
            aria-controls={`panel-${value}`}
            onClick={() => setTab(value)}
            className={`-mb-px rounded-t-lg border-b-2 px-4 py-2 text-sm font-medium transition ${
              tab === value
                ? "border-indigo-600 text-indigo-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t(`admin.tab.${value}`)}
          </button>
        ))}
      </div>

      {tab === "users" && (
        <div role="tabpanel" id="panel-users" aria-labelledby="tab-users">
          <UsersTab currentUserId={user.id} />
        </div>
      )}
      {tab === "ai" && (
        <div role="tabpanel" id="panel-ai" aria-labelledby="tab-ai">
          <AiUsageTab locale={locale} />
        </div>
      )}
      {tab === "audit" && (
        <div role="tabpanel" id="panel-audit" aria-labelledby="tab-audit">
          <AuditTab locale={locale} />
        </div>
      )}
    </div>
  );
}

function UsersTab({ currentUserId }: { currentUserId: number }) {
  const { t, lang } = useI18n();
  const qc = useQueryClient();
  const [input, setInput] = useState("");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);

  const locale = lang === "ar" ? "ar" : "en";

  const users = useQuery({
    queryKey: ["admin", "users", q, page],
    queryFn: () => api.listAdminUsers(q, page, PAGE_SIZE),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin", "users"] });

  const deactivate = useMutation({
    mutationFn: (id: number) => api.deactivateAdminUser(id),
    onSuccess: invalidate,
  });
  const reactivate = useMutation({
    mutationFn: (id: number) => api.reactivateAdminUser(id),
    onSuccess: invalidate,
  });

  function onSearch(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setQ(input.trim());
  }

  const total = users.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const busy = deactivate.isPending || reactivate.isPending;

  return (
    <div className="space-y-4">
      <form onSubmit={onSearch} className="flex flex-wrap items-end gap-2">
        <div className="min-w-56 flex-1">
          <label
            htmlFor="admin-search"
            className="mb-1 block text-sm font-medium text-slate-700"
          >
            {t("admin.search")}
          </label>
          <input
            id="admin-search"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t("admin.search")}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <Button type="submit">{t("admin.searchAction")}</Button>
      </form>

      {users.isLoading && <Spinner label={t("common.loading")} />}
      {users.isError && <ErrorText>{(users.error as Error).message}</ErrorText>}

      {deactivate.isError && (
        <ErrorText>{(deactivate.error as Error).message}</ErrorText>
      )}
      {reactivate.isError && (
        <ErrorText>{(reactivate.error as Error).message}</ErrorText>
      )}

      {users.data && (
        <>
          <p className="text-sm text-slate-500">
            {t("admin.total", { n: total })}
          </p>

          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-start text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-4 py-2 text-start">{t("admin.email")}</th>
                  <th scope="col" className="px-4 py-2 text-start">{t("admin.name")}</th>
                  <th scope="col" className="px-4 py-2 text-start">{t("admin.role")}</th>
                  <th scope="col" className="px-4 py-2 text-start">{t("admin.grade")}</th>
                  <th scope="col" className="px-4 py-2 text-start">{t("admin.status")}</th>
                  <th scope="col" className="px-4 py-2 text-start">{t("admin.created")}</th>
                  <th scope="col" className="px-4 py-2 text-start">{t("admin.actions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.data.items.map((u: User) => (
                  <tr key={u.id}>
                    <td className="px-4 py-2 font-medium text-slate-800">
                      {u.email}
                    </td>
                    <td className="px-4 py-2 text-slate-600">{u.display_name}</td>
                    <td className="px-4 py-2 text-slate-600">{u.role}</td>
                    <td className="px-4 py-2 text-slate-600">{u.grade ?? "—"}</td>
                    <td className="px-4 py-2">
                      {u.is_active ? (
                        <Badge value="ready" />
                      ) : (
                        <Badge value="failed" />
                      )}
                      <span className="sr-only">
                        {u.is_active ? t("admin.active") : t("admin.inactive")}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-500">
                      {new Date(u.created_at).toLocaleDateString(locale)}
                    </td>
                    <td className="px-4 py-2">
                      {u.id === currentUserId ? (
                        <span className="text-xs text-slate-400">
                          {t("admin.you")}
                        </span>
                      ) : u.is_active ? (
                        <Button
                          variant="secondary"
                          disabled={busy}
                          onClick={() => deactivate.mutate(u.id)}
                        >
                          {t("admin.deactivate")}
                        </Button>
                      ) : (
                        <Button
                          variant="secondary"
                          disabled={busy}
                          onClick={() => reactivate.mutate(u.id)}
                        >
                          {t("admin.reactivate")}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {users.data.items.length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-4 py-6 text-center text-slate-500"
                    >
                      {t("admin.empty")}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between gap-3">
            <span className="text-sm text-slate-500">
              {t("admin.page", { page, pages })}
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                {t("admin.prev")}
              </Button>
              <Button
                variant="secondary"
                disabled={page >= pages}
                onClick={() => setPage((p) => p + 1)}
              >
                {t("admin.next")}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function AiUsageTab({ locale }: { locale: string }) {
  const { t } = useI18n();

  const usage = useQuery({
    queryKey: ["admin", "ai-usage"],
    queryFn: () => api.listAiUsage(100),
  });

  if (usage.isLoading) return <Spinner label={t("common.loading")} />;
  if (usage.isError)
    return <ErrorText>{(usage.error as Error).message}</ErrorText>;

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.when")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.provider")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.model")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.operation")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.tokens")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.latency")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.status")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {usage.data?.map((row) => (
            <tr key={row.id}>
              <td className="whitespace-nowrap px-4 py-2 text-slate-500">
                {new Date(row.created_at).toLocaleString(locale)}
              </td>
              <td className="px-4 py-2 text-slate-600">{row.provider}</td>
              <td className="px-4 py-2 text-slate-600">{row.model}</td>
              <td className="px-4 py-2 text-slate-600">{row.operation}</td>
              <td className="px-4 py-2 text-slate-600">
                {row.prompt_tokens + row.completion_tokens}
              </td>
              <td className="px-4 py-2 text-slate-600">
                {t("admin.ms", { n: row.latency_ms })}
              </td>
              <td className="px-4 py-2">
                {row.status === "ok" ? (
                  <Badge value="ready" />
                ) : (
                  <span title={row.error ?? ""}>
                    <Badge value="failed" />
                    <span className="sr-only">{row.error ?? t("common.error")}</span>
                  </span>
                )}
              </td>
            </tr>
          ))}
          {usage.data?.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                {t("admin.empty")}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function AuditTab({ locale }: { locale: string }) {
  const { t } = useI18n();

  const logs = useQuery({
    queryKey: ["admin", "audit-logs"],
    queryFn: () => api.listAuditLogs(100),
  });

  if (logs.isLoading) return <Spinner label={t("common.loading")} />;
  if (logs.isError) return <ErrorText>{(logs.error as Error).message}</ErrorText>;

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.when")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.actor")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.action")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.target")}</th>
            <th scope="col" className="px-4 py-2 text-start">{t("admin.details")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {logs.data?.map((row) => (
            <tr key={row.id}>
              <td className="whitespace-nowrap px-4 py-2 text-slate-500">
                {new Date(row.created_at).toLocaleString(locale)}
              </td>
              <td className="px-4 py-2 text-slate-600">
                {row.actor_user_id ?? "—"}
              </td>
              <td className="px-4 py-2 font-medium text-slate-800">
                {row.action}
              </td>
              <td className="px-4 py-2 text-slate-600">
                {row.target_type}
                {row.target_id ? `#${row.target_id}` : ""}
              </td>
              <td className="px-4 py-2 text-xs text-slate-500">
                {Object.keys(row.meta).length
                  ? JSON.stringify(row.meta)
                  : "—"}
              </td>
            </tr>
          ))}
          {logs.data?.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                {t("admin.empty")}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

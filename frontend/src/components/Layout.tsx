import { useEffect, useRef } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n } from "../i18n";
import { ResponsiveNav } from "./ResponsiveNav";
import { Button } from "./ui";

const NAV = [
  { to: "/", key: "nav.dashboard", icon: "⌂", end: true },
  { to: "/library", key: "nav.library", icon: "▤" },
  { to: "/upload", key: "nav.upload", icon: "+" },
  { to: "/tutor", key: "nav.tutor", icon: "✦" },
  { to: "/reviews", key: "nav.reviews", icon: "↻" },
  { to: "/planner", key: "nav.planner", icon: "▦" },
  { to: "/progress", key: "nav.progress", icon: "↗" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const { t, lang, setLanguage } = useI18n();
  const location = useLocation();
  const mainRef = useRef<HTMLElement>(null);

  const notifications = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => api.listNotifications(false, 1),
    refetchInterval: 60_000,
  });
  const unread = notifications.data?.unread ?? 0;

  useEffect(() => {
    mainRef.current?.focus();
    window.scrollTo({ top: 0 });
  }, [location.pathname]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void api.recordStudyTime(60).catch((error: unknown) => {
          console.error("Failed to record study time", error);
        });
      }
    }, 60_000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="app-shell min-h-screen bg-slate-50 text-slate-900">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:start-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:shadow"
      >
        {t("nav.skip")}
      </a>

      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur-sm">
        <div className="flex min-h-[68px] items-center gap-4 px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2 min-h-[44px]">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-sm font-bold text-white shadow-md shadow-indigo-200">
              S
            </span>
            <span>
              <span className="block text-base font-bold leading-tight tracking-tight">Suhail</span>
              <span className="hidden text-[10px] font-medium uppercase tracking-[0.16em] text-slate-400 sm:block">
                Smart Teacher
              </span>
            </span>
          </Link>

          <div className="ms-auto flex items-center gap-2">
            <label className="sr-only" htmlFor="language-select">
              {t("nav.language")}
            </label>
            <select
              id="language-select"
              value={lang}
              onChange={(e) => setLanguage(e.target.value as "en" | "ar")}
              className="min-h-[44px] rounded-xl border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-600"
            >
              <option value="en">English</option>
              <option value="ar">العربية</option>
            </select>

            <NavLink
              to="/notifications"
              aria-label={
                unread > 0
                  ? `${t("nav.notifications")}, ${t("notifications.unread", { n: unread })}`
                  : t("nav.notifications")
              }
              className={({ isActive }) =>
                `relative flex min-h-[44px] items-center rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              <span aria-hidden="true">🔔</span>
              {unread > 0 && (
                <span
                  aria-hidden="true"
                  className="absolute -end-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white"
                >
                  {unread > 99 ? "99+" : unread}
                </span>
              )}
            </NavLink>

            <NavLink
              to="/settings"
              aria-label={`${t("nav.settings")}: ${user?.display_name ?? ""}`}
              className="hidden min-h-[44px] items-center rounded-xl px-3 text-sm font-medium text-slate-600 hover:bg-slate-100 sm:flex"
            >
              <span className="me-2 grid h-7 w-7 place-items-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">
                {user?.display_name?.trim().charAt(0).toUpperCase() || "S"}
              </span>
              {user?.display_name}
            </NavLink>
            <Button variant="secondary" onClick={() => void logout()} className="min-h-[44px] rounded-xl">
              {t("common.signOut")}
            </Button>
          </div>
        </div>
      </header>

      <aside className="fixed inset-y-[68px] start-0 z-30 hidden w-64 flex-col border-e border-slate-200 bg-white px-4 py-6 md:flex">
        <p className="px-3 pb-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
          {t("nav.workspace")}
        </p>
        <nav aria-label={t("nav.primary")} className="flex-1 space-y-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `group flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-semibold transition ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700 shadow-sm shadow-indigo-100"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`
              }
            >
              <span
                aria-hidden="true"
                className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-base text-slate-500 transition group-hover:bg-white"
              >
                {item.icon}
              </span>
              {t(item.key)}
            </NavLink>
          ))}
          {user?.role === "admin" && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `group flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-semibold transition ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700 shadow-sm shadow-indigo-100"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`
              }
            >
              <span aria-hidden="true" className="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-slate-500">
                ⚙
              </span>
              {t("nav.admin")}
            </NavLink>
          )}
        </nav>
        <div className="mt-5 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 p-4 text-white shadow-lg shadow-indigo-200/70">
          <p className="text-sm font-bold">{t("dashboard.askTutor")}</p>
          <p className="mt-1 text-xs leading-relaxed text-indigo-100">
            {t("tutor.subtitle")}
          </p>
          <Link
            to="/tutor"
            className="mt-3 inline-flex min-h-9 items-center rounded-lg bg-white/15 px-3 text-xs font-semibold text-white transition hover:bg-white/25"
          >
            {t("nav.tutor")} <span aria-hidden="true" className="ms-2">→</span>
          </Link>
        </div>
      </aside>

      <main
        id="main"
        ref={mainRef}
        tabIndex={-1}
        className="mx-auto max-w-6xl px-4 py-6 pb-28 focus:outline-none sm:px-6 sm:py-8 sm:pb-8 md:ms-64"
      >
        <Outlet />
      </main>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 px-3 pb-[calc(env(safe-area-inset-bottom)+0.75rem)] pt-3 shadow-[0_-10px_30px_rgba(15,23,42,0.08)] backdrop-blur-sm md:hidden">
        <ResponsiveNav />
      </div>
    </div>
  );
}

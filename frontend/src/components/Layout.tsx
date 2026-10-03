import { useEffect, useRef } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n } from "../i18n";
import { ResponsiveNav } from "./ResponsiveNav";
import { Button } from "./ui";

const NAV = [
  { to: "/", key: "nav.dashboard", end: true },
  { to: "/library", key: "nav.library" },
  { to: "/tutor", key: "nav.tutor" },
  { to: "/reviews", key: "nav.reviews" },
  { to: "/planner", key: "nav.planner" },
  { to: "/progress", key: "nav.progress" },
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

  return (
    <div className="app-shell min-h-screen bg-slate-50 text-slate-900">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:start-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:shadow"
      >
        {t("nav.skip")}
      </a>

      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-3 px-4 py-3 sm:px-6 sm:py-4">
          <Link to="/" className="flex items-center gap-2 min-h-[44px]">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
              S
            </span>
            <span className="text-lg font-semibold">Suhail</span>
          </Link>

          <nav
            aria-label={t("nav.primary")}
            className="order-last hidden w-full flex-wrap items-center gap-1 sm:order-none sm:flex sm:w-auto"
          >
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {t(item.key)}
              </NavLink>
            ))}
            {user?.role === "admin" && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {t("nav.admin")}
              </NavLink>
            )}
          </nav>

          <div className="ms-auto flex items-center gap-2">
            <label className="sr-only" htmlFor="language-select">
              {t("nav.language")}
            </label>
            <select
              id="language-select"
              value={lang}
              onChange={(e) => setLanguage(e.target.value as "en" | "ar")}
              className="min-h-[44px] rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-600"
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
              className="min-h-[44px] self-center text-sm text-slate-500 hover:text-slate-700"
            >
              {user?.display_name}
            </NavLink>
            <Button variant="secondary" onClick={() => void logout()} className="min-h-[44px]">
              {t("common.signOut")}
            </Button>
          </div>
        </div>
      </header>

      <main
        id="main"
        ref={mainRef}
        tabIndex={-1}
        className="mx-auto max-w-6xl px-4 py-6 pb-28 focus:outline-none sm:px-6 sm:py-8 sm:pb-8"
      >
        <Outlet />
      </main>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 px-3 pb-[calc(env(safe-area-inset-bottom)+0.75rem)] pt-3 shadow-[0_-10px_30px_rgba(15,23,42,0.08)] backdrop-blur-sm sm:hidden">
        <ResponsiveNav />
      </div>
    </div>
  );
}

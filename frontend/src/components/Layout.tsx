import { useEffect, useRef } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n } from "../i18n";
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
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:start-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:shadow"
      >
        {t("nav.skip")}
      </a>

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-6 py-4">
          <Link to="/" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
              S
            </span>
            <span className="text-lg font-semibold">Suhail</span>
          </Link>

          <nav
            aria-label={t("nav.primary")}
            className="order-last flex w-full flex-wrap items-center gap-1 sm:order-none sm:w-auto"
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
              className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-600"
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
                `relative rounded-lg px-3 py-1.5 text-sm font-medium transition ${
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
              className="text-sm text-slate-500 hover:text-slate-700"
            >
              {user?.display_name}
            </NavLink>
            <Button variant="secondary" onClick={() => void logout()}>
              {t("common.signOut")}
            </Button>
          </div>
        </div>
      </header>

      <main
        id="main"
        ref={mainRef}
        tabIndex={-1}
        className="mx-auto max-w-6xl px-6 py-8 focus:outline-none"
      >
        <Outlet />
      </main>
    </div>
  );
}

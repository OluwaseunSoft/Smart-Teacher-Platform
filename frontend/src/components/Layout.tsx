import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n } from "../i18n";
import { ResponsiveNav } from "./ResponsiveNav";
import { Icon } from "./Icon";
import { navigation } from "./navigation";

export default function Layout() {
  const { user, logout } = useAuth();
  const { t, lang, setLanguage } = useI18n();
  const location = useLocation();
  const mainRef = useRef<HTMLElement>(null);
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    try { return localStorage.getItem("suhail.theme") === "light" ? "light" : "dark"; }
    catch { return "dark"; }
  });
  const notifications = useQuery({
    queryKey: ["notifications", "unread"], queryFn: () => api.listNotifications(false, 1), refetchInterval: 60_000,
  });
  const unread = notifications.data?.unread ?? 0;
  const current = navigation.find(item => item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to));

  useEffect(() => {
    mainRef.current?.focus();
    window.scrollTo({ top: 0 });
  }, [location.pathname]);
  useEffect(() => {
    try { localStorage.setItem("suhail.theme", theme); } catch { /* Theme still works without storage. */ }
    const meta = document.querySelector('meta[name="theme-color"]');
    const previous = meta?.getAttribute("content");
    meta?.setAttribute("content", theme === "dark" ? "#080b14" : "#f0f4ff");
    return () => { if (previous) meta?.setAttribute("content", previous); };
  }, [theme]);
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void api.recordStudyTime(60).catch((error: unknown) => console.error("Failed to record study time", error));
      }
    }, 60_000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="app-shell" data-theme={theme}>
      <a href="#main" className="skip-link">{t("nav.skip")}</a>
      <aside className="study-sidebar">
        <Link to="/" className="study-brand">
          <span className="brand-mark"><Icon name="sparkles" size={25}/></span>
          <span><strong>Suhail<span className="brand-dot">.</span></strong><small>{t("shell.smartStudy")}</small></span>
        </Link>
        <div className="sidebar-content">
          <p className="eyebrow nav-caption">{t("shell.learn")}</p>
          <nav aria-label={t("nav.primary")}>
            {navigation.map(item => <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `side-link ${isActive ? "is-active" : ""}`}>
              <Icon name={item.icon}/><span>{t(item.key)}</span>
              {item.to === "/tutor" && <span className="ai-chip">AI</span>}
            </NavLink>)}
          </nav>
          <div className="sidebar-tip">
            <span className="icon-tile tone-teal"><Icon name="sparkles"/></span>
            <h2>{t("shell.stuck")}</h2><p>{t("shell.tutorHelp")}</p>
            <Link to="/tutor" className="text-link">{t("dashboard.askTutor")}<Icon name="arrow" size={16}/></Link>
          </div>
          <div className="sidebar-settings">
            {user?.role === "admin" && <NavLink to="/admin" className="side-link"><Icon name="settings"/>{t("nav.admin")}</NavLink>}
            <NavLink to="/settings" className={({ isActive }) => `side-link ${isActive ? "is-active" : ""}`}><Icon name="settings"/>{t("nav.settings")}</NavLink>
          </div>
        </div>
        <Link to="/settings" className="sidebar-profile">
          <span className="profile-avatar">{user?.display_name?.trim().charAt(0).toUpperCase() || "S"}</span>
          <span><strong>{user?.display_name}</strong><small>{t("shell.yourSpace")}</small></span><Icon name="arrow" size={16}/>
        </Link>
      </aside>

      <div className="study-workspace">
        <header className="study-topbar">
          <Link to="/" className="mobile-brand" aria-label="Suhail"><span className="brand-mark"><Icon name="sparkles"/></span></Link>
          <div className="topbar-page"><span className="eyebrow">{t("shell.yourSpace")}</span><strong>{t(current?.key ?? (location.pathname === "/settings" ? "nav.settings" : location.pathname === "/notifications" ? "nav.notifications" : "shell.keepLearning"))}</strong></div>
          <div className="topbar-actions">
            <label className="sr-only" htmlFor="language-select">{t("nav.language")}</label>
            <select id="language-select" value={lang} onChange={e => setLanguage(e.target.value as "en" | "ar")} className="language-select">
              <option value="en">English</option><option value="ar">العربية</option>
            </select>
            <button type="button" className="shell-icon-button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={t(theme === "dark" ? "shell.lightMode" : "shell.darkMode")} title={t(theme === "dark" ? "shell.lightMode" : "shell.darkMode")}><Icon name={theme === "dark" ? "sun" : "moon"}/></button>
            <NavLink to="/notifications" className="shell-icon-button notification-button" aria-label={unread ? `${t("nav.notifications")}, ${t("notifications.unread", { n: unread })}` : t("nav.notifications")}>
              <Icon name="bell"/>{unread > 0 && <span className="notification-count" aria-hidden="true">{unread > 99 ? "99+" : unread}</span>}
            </NavLink>
            <button type="button" className="shell-icon-button sign-out-button" onClick={() => void logout()} aria-label={t("common.signOut")} title={t("common.signOut")}><Icon name="logout"/></button>
          </div>
        </header>
        <main id="main" ref={mainRef} tabIndex={-1} className="study-main"><Outlet/></main>
      </div>
      <ResponsiveNav/>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useI18n } from "../i18n";
import { useAuth } from "../auth";
import { Icon } from "./Icon";
import { navigation } from "./navigation";

export function ResponsiveNav() {
  const { t } = useI18n();
  const { user, logout } = useAuth();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  const container = useRef<HTMLDivElement>(null);
  const primary = navigation.filter(item => ["/", "/library", "/tutor", "/reviews"].includes(item.to));
  const more = [...navigation.filter(item => !primary.includes(item)),
    { to: "/settings", key: "nav.settings", icon: "settings" as const },
    ...(user?.role === "admin" ? [{ to: "/admin", key: "nav.admin", icon: "settings" as const }] : []),
  ];
  useEffect(() => { setOpen(false); }, [location.pathname]);
  useEffect(() => {
    if (!open) return;
    container.current?.querySelector<HTMLAnchorElement>("#more-navigation a")?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") { setOpen(false); toggle.current?.focus(); }
    }
    function onPointer(event: PointerEvent) {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => { document.removeEventListener("keydown", onKey); document.removeEventListener("pointerdown", onPointer); };
  }, [open]);
  return <div className="mobile-navigation" ref={container}>
    {open && <nav id="more-navigation" aria-label={t("shell.more")} className="mobile-more-panel">
      <div className="more-heading"><strong>{t("shell.more")}</strong><button className="shell-icon-button" onClick={() => { setOpen(false); toggle.current?.focus(); }} aria-label={t("common.close")}><Icon name="close"/></button></div>
      {more.map(item => <NavLink key={item.to} to={item.to} className={({ isActive }) => `side-link ${isActive ? "is-active" : ""}`}><Icon name={item.icon}/>{t(item.key)}</NavLink>)}
      <button type="button" className="side-link w-full" onClick={() => void logout()}><Icon name="logout"/>{t("common.signOut")}</button>
    </nav>}
    <nav aria-label={t("nav.primary")} className="mobile-tabs">
      {primary.map(item => <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `mobile-tab ${isActive ? "is-active" : ""}`}><Icon name={item.icon}/><span>{t(item.key)}</span></NavLink>)}
      <button ref={toggle} type="button" aria-expanded={open} aria-controls="more-navigation" className={`mobile-tab ${open || more.some(item => location.pathname.startsWith(item.to)) ? "is-active" : ""}`} onClick={() => setOpen(!open)}><Icon name="more"/><span>{t("shell.more")}</span></button>
    </nav>
  </div>;
}

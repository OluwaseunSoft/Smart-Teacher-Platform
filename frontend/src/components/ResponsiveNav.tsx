import { NavLink } from "react-router-dom";
import { useI18n } from "../i18n";

const NAV_ITEMS = [
  { to: "/", key: "nav.dashboard", exact: true },
  { to: "/library", key: "nav.library" },
  { to: "/upload", key: "nav.upload" },
  { to: "/tutor", key: "nav.tutor" },
  { to: "/reviews", key: "nav.reviews" },
  { to: "/planner", key: "nav.planner" },
  { to: "/progress", key: "nav.progress" },
];

export function ResponsiveNav() {
  const { t } = useI18n();

  return (
    <nav aria-label={t("nav.primary")} className="md:hidden">
      <ul className="grid grid-cols-3 gap-2 rounded-2xl border border-slate-200 bg-white/95 p-2 shadow-lg shadow-slate-200/60 backdrop-blur-sm">
        {NAV_ITEMS.map(({ to, key, exact }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={exact}
              className={({ isActive }) =>
                `flex min-h-[48px] items-center justify-center rounded-xl px-2 py-2 text-center text-[11px] font-medium leading-tight transition ${
                  isActive
                    ? "bg-indigo-100 text-indigo-700"
                    : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {t(key)}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

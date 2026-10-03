import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", exact: true },
  { to: "/library", label: "Library" },
  { to: "/tutor", label: "Tutor" },
  { to: "/reviews", label: "Reviews" },
  { to: "/planner", label: "Planner" },
  { to: "/progress", label: "Progress" },
];

export function ResponsiveNav() {
  return (
    <nav aria-label="Mobile primary navigation" className="sm:hidden">
      <ul className="grid grid-cols-3 gap-2 rounded-2xl border border-slate-200 bg-white/95 p-2 shadow-lg shadow-slate-200/60 backdrop-blur-sm">
        {NAV_ITEMS.map(({ to, label, exact }) => (
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
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}

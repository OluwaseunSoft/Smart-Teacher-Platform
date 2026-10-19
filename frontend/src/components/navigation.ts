import type { IconName } from "./Icon";

export const navigation: { to: string; key: string; icon: IconName; end?: boolean }[] = [
  { to: "/", key: "nav.dashboard", icon: "home", end: true },
  { to: "/library", key: "nav.library", icon: "book" },
  { to: "/upload", key: "nav.upload", icon: "upload" },
  { to: "/tutor", key: "nav.tutor", icon: "sparkles" },
  { to: "/reviews", key: "nav.reviews", icon: "review" },
  { to: "/planner", key: "nav.planner", icon: "calendar" },
  { to: "/progress", key: "nav.progress", icon: "chart" },
];

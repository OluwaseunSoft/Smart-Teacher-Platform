import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

import App from "../../App";

vi.mock("../../auth", () => ({
  useAuth: () => ({
    user: {
      id: 1,
      email: "student@example.com",
      display_name: "Ada",
      role: "student",
      grade: 10,
      language: "en",
    },
    loading: false,
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  }),
}));

vi.mock("../../i18n", () => ({
  useI18n: () => ({
    t: (key: string) => ({
      "nav.skip": "Skip to content",
      "nav.primary": "Primary navigation",
      "dashboard.plan": "Dashboard plan",
      "dashboard.welcome": "Welcome back, Ada",
      "dashboard.subtitle": "Here is where you stand today.",
      "dashboard.streak": "Day streak",
      "dashboard.longest": "Longest 5",
      "dashboard.topics": "Topics covered",
      "dashboard.mastery": "Average mastery",
      "dashboard.due": "Reviews due",
      "dashboard.makePlan": "Build a study plan",
      "dashboard.startReview": "Start reviewing",
      "dashboard.askTutor": "Ask the tutor",
      "dashboard.achievements": "Achievements",
      "nav.notifications": "Notifications",
      "nav.language": "Language",
      "common.signOut": "Sign out",
      "notifications.unread": "1 unread",
    })[key] ?? key,
    lang: "en",
    setLanguage: vi.fn(),
  }),
}));

vi.mock("../../api/client", () => ({
  api: {
    listNotifications: vi.fn().mockResolvedValue({ unread: 0 }),
    getDashboard: vi.fn().mockResolvedValue({
      streak: { current: 4, longest: 5 },
      topics_covered: 3,
      topics_total: 5,
      average_mastery: 0.72,
      due_reviews: 2,
      achievements_unlocked: 1,
      achievements_total: 4,
      active_plan: { completed_items: 1, total_items: 3, percent_complete: 33 },
    }),
  },
}));

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Suhail app accessibility basics", () => {
  it("renders a skip-to-content link and primary navigation landmarks", () => {
    renderApp();

    expect(screen.getByRole("link", { name: /skip to content/i })).toBeInTheDocument();
    expect(screen.getAllByRole("navigation", { name: /primary navigation/i }).length).toBeGreaterThan(0);
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("provides accessible names for dashboard and progress interactions", async () => {
    renderApp();

    expect(await screen.findByText(/Welcome back, Ada/i)).toBeInTheDocument();
    expect(screen.getByText(/Build a study plan/i)).toBeInTheDocument();
  });
});


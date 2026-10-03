import { useEffect, type ReactNode } from "react";
import {
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import { useAuth } from "./auth";
import { useI18n, type Language } from "./i18n";
import { isOnboarded } from "./lib/onboarding";
import { Spinner } from "./components/ui";
import Layout from "./components/Layout";
import AdminPage from "./pages/AdminPage";
import DashboardPage from "./pages/DashboardPage";
import FlashcardPage from "./pages/FlashcardPage";
import LandingPage from "./pages/LandingPage";
import LessonPage from "./pages/LessonPage";
import LoginPage from "./pages/LoginPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import MaterialDetailPage from "./pages/MaterialDetailPage";
import MaterialsPage from "./pages/MaterialsPage";
import NotificationsPage from "./pages/NotificationsPage";
import OnboardingPage from "./pages/OnboardingPage";
import PlannerPage from "./pages/PlannerPage";
import ProgressPage from "./pages/ProgressPage";
import QuizPage from "./pages/QuizPage";
import ReviewsPage from "./pages/ReviewsPage";
import SettingsPage from "./pages/SettingsPage";
import StudyPage from "./pages/StudyPage";
import TopicPage from "./pages/TopicPage";
import TutorPage from "./pages/TutorPage";

function RequireAdmin({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "admin") return <Navigate to="/" replace />;
  return <>{children}</>;
}

function RequireOnboarding({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const location = useLocation();
  if (
    user &&
    user.role === "student" &&
    user.grade === null &&
    !isOnboarded(user.id) &&
    location.pathname !== "/onboarding"
  ) {
    return <Navigate to="/onboarding" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  const { user, loading } = useAuth();
  const { setLanguage } = useI18n();

  useEffect(() => {
    if (user && (user.language === "en" || user.language === "ar")) {
      setLanguage(user.language as Language);
    }
  }, [user, setLanguage]);

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50">
        <Spinner label="Loading…" />
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route
        path="/onboarding"
        element={
          isOnboarded(user.id) ? (
            <Navigate to="/" replace />
          ) : (
            <OnboardingPage />
          )
        }
      />
      <Route
        element={
          <RequireOnboarding>
            <Layout />
          </RequireOnboarding>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/library" element={<MaterialsPage />} />
        <Route path="/materials/:materialId" element={<MaterialDetailPage />} />
        <Route path="/lessons/:lessonId" element={<LessonPage />} />
        <Route path="/lessons/:lessonId/quiz" element={<QuizPage />} />
        <Route path="/topics/:topicId" element={<TopicPage />} />
        <Route path="/study/:sessionId" element={<StudyPage />} />
        <Route path="/flashcards" element={<FlashcardPage />} />
        <Route path="/tutor" element={<TutorPage />} />
        <Route path="/reviews" element={<ReviewsPage />} />
        <Route path="/planner" element={<PlannerPage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route
          path="/admin"
          element={
            <RequireAdmin>
              <AdminPage />
            </RequireAdmin>
          }
        />
        <Route
          path="*"
          element={<p className="text-slate-500">Not found.</p>}
        />
      </Route>
    </Routes>
  );
}

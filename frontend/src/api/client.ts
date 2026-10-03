import type {
  Achievement,
  AdminUserPage,
  AdminUserUpdate,
  AIUsageLog,
  AppNotification,
  AuditLog,
  Concept,
  Curriculum,
  Dashboard,
  ExamDate,
  Lesson,
  LessonSummary,
  Material,
  MasteryEvent,
  NextAction,
  NotificationPage,
  Plan,
  PlanDetail,
  PlanItem,
  PlanSummary,
  ProfileUpdate,
  Quiz,
  QuizResult,
  ReviewQueue,
  ReviewSchedule,
  ReviewSummary,
  Streak,
  StudySession,
  TokenResponse,
  TopicDetail,
  TopicMastery,
  TutorConversation,
  TutorConversationDetail,
  TutorConversationSummary,
  TutorReply,
  User,
} from "../types";
import { clearTokens, getAccessToken } from "./authToken";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (res.status === 401) {
    clearTokens();
    window.dispatchEvent(new Event("suhail:unauthorized"));
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  signup: (payload: {
    email: string;
    password: string;
    display_name: string;
  }) =>
    request<TokenResponse>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  requestPasswordReset: (email: string) =>
    request<{ detail: string; reset_token?: string }>("/auth/password-reset/request", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  confirmPasswordReset: (token: string, newPassword: string) =>
    request<{ detail: string }>("/auth/password-reset/confirm", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    }),

  logout: () => request<void>("/auth/logout", { method: "POST" }),

  me: () => request<User>("/auth/me"),

  health: () =>
    request<{ status: string; llm_provider: string; embedding_provider: string }>(
      "/health",
    ),

  listMaterials: () => request<Material[]>("/materials"),

  getMaterial: (id: number) => request<Material>(`/materials/${id}`),

  createTextMaterial: (title: string, text: string) =>
    request<Material>("/materials/text", {
      method: "POST",
      body: JSON.stringify({ title, text }),
    }),

  uploadFile: (file: File, title?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    return request<Material>("/materials", { method: "POST", body: form });
  },

  processMaterial: (id: number) =>
    request<Material>(`/materials/${id}/process`, { method: "POST" }),

  deleteMaterial: (id: number) =>
    request<void>(`/materials/${id}`, { method: "DELETE" }),

  listConcepts: (id: number) => request<Concept[]>(`/materials/${id}/concepts`),

  listLessons: (id: number) =>
    request<LessonSummary[]>(`/materials/${id}/lessons`),

  getLesson: (id: number) => request<Lesson>(`/lessons/${id}`),

  regenerateLesson: (id: number, simpler = false) =>
    request<Lesson>(`/lessons/${id}/regenerate`, {
      method: "POST",
      body: JSON.stringify({ simpler }),
    }),

  createQuiz: (lessonId: number) =>
    request<Quiz>(`/lessons/${lessonId}/quiz`, { method: "POST" }),

  getQuiz: (lessonId: number) => request<Quiz>(`/lessons/${lessonId}/quiz`),

  submitQuiz: (
    lessonId: number,
    answers: { question_id: number; response: string }[],
  ) =>
    request<QuizResult>(`/quizzes/${lessonId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),

  createSession: (materialId: number) =>
    request<StudySession>("/sessions", {
      method: "POST",
      body: JSON.stringify({ material_id: materialId }),
    }),

  getSession: (id: number) => request<StudySession>(`/sessions/${id}`),

  nextStep: (id: number) =>
    request<NextAction>(`/sessions/${id}/next`, { method: "POST" }),

  updateProfile: (payload: ProfileUpdate) =>
    request<User>("/auth/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  listCurriculum: () => request<Curriculum[]>("/curriculum"),

  getTopic: (id: number) => request<TopicDetail>(`/topics/${id}`),

  materialCurriculum: (materialId: number) =>
    request<Curriculum>(`/curriculum/materials/${materialId}`),

  listMastery: () => request<TopicMastery[]>("/mastery"),

  topicHistory: (topicId: number) =>
    request<MasteryEvent[]>(`/mastery/topics/${topicId}/history`),

  reviewSummary: () => request<ReviewSummary>("/reviews/summary"),

  reviewQueue: (limit = 20) =>
    request<ReviewQueue>(`/reviews/queue?limit=${limit}`),

  listReviews: (dueOnly = false) =>
    request<ReviewQueue>(`/reviews?due_only=${dueOnly}`),

  submitReview: (topicId: number, quality: number) =>
    request<ReviewSchedule>(`/reviews/${topicId}`, {
      method: "POST",
      body: JSON.stringify({ quality }),
    }),

  listTutorConversations: () =>
    request<TutorConversationSummary[]>("/tutor/conversations"),

  createTutorConversation: (payload: {
    topic_id?: number | null;
    title?: string;
    language?: "en" | "ar";
  }) =>
    request<TutorConversation>("/tutor/conversations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getTutorConversation: (id: number) =>
    request<TutorConversationDetail>(`/tutor/conversations/${id}`),

  sendTutorMessage: (id: number, content: string) =>
    request<TutorReply>(`/tutor/conversations/${id}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),

  deleteTutorConversation: (id: number) =>
    request<void>(`/tutor/conversations/${id}`, { method: "DELETE" }),

  listExams: () => request<ExamDate[]>("/planner/exams"),

  createExam: (payload: {
    title: string;
    exam_date: string;
    subject_id?: number | null;
  }) =>
    request<ExamDate>("/planner/exams", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteExam: (id: number) =>
    request<void>(`/planner/exams/${id}`, { method: "DELETE" }),

  generatePlan: (payload: {
    exam_date_id: number;
    daily_minutes?: number;
    subject_id?: number | null;
  }) =>
    request<Plan>("/planner/plans", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listPlans: () => request<PlanSummary[]>("/planner/plans"),

  getPlan: (id: number) => request<PlanDetail>(`/planner/plans/${id}`),

  updatePlanItem: (planId: number, itemId: number, status: "pending" | "done") =>
    request<PlanItem>(`/planner/plans/${planId}/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  deletePlan: (id: number) =>
    request<void>(`/planner/plans/${id}`, { method: "DELETE" }),

  getStreak: () => request<Streak>("/gamification/streak"),

  getAchievements: () =>
    request<Achievement[]>("/gamification/achievements"),

  getDashboard: () => request<Dashboard>("/gamification/dashboard"),

  listNotifications: (unreadOnly = false, limit = 50) =>
    request<NotificationPage>(
      `/notifications?unread_only=${unreadOnly}&limit=${limit}`,
    ),

  markAllNotificationsRead: () =>
    request<{ updated: number }>("/notifications/read-all", { method: "POST" }),

  markNotificationRead: (id: number) =>
    request<AppNotification>(`/notifications/${id}/read`, { method: "POST" }),

  listAdminUsers: (q = "", page = 1, pageSize = 20) =>
    request<AdminUserPage>(
      `/admin/users?q=${encodeURIComponent(q)}&page=${page}&page_size=${pageSize}`,
    ),

  updateAdminUser: (id: number, payload: AdminUserUpdate) =>
    request<User>(`/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deactivateAdminUser: (id: number) =>
    request<User>(`/admin/users/${id}/deactivate`, { method: "POST" }),

  reactivateAdminUser: (id: number) =>
    request<User>(`/admin/users/${id}/reactivate`, { method: "POST" }),

  listAiUsage: (limit = 50) =>
    request<AIUsageLog[]>(`/admin/ai-usage?limit=${limit}`),

  listAuditLogs: (limit = 50) =>
    request<AuditLog[]>(`/admin/audit-logs?limit=${limit}`),
};

export type MaterialStatus = "uploaded" | "processing" | "ready" | "failed";

export interface Material {
  id: number;
  title: string;
  source_type: string;
  filename: string | null;
  status: MaterialStatus;
  error: string | null;
  created_at: string;
}

export interface Concept {
  id: number;
  material_id: number;
  parent_id: number | null;
  title: string;
  summary: string;
  order_index: number;
  difficulty: string;
}

export interface Lesson {
  id: number;
  material_id: number;
  concept_id: number;
  title: string;
  objectives: string[];
  content: string;
  status: string;
}

export interface LessonSummary {
  id: number;
  concept_id: number;
  title: string;
  status: string;
}

export interface QuizQuestion {
  id: number;
  type: "mcq" | "short";
  prompt: string;
  options: string[] | null;
  difficulty: number;
}

export interface Quiz {
  lesson_id: number;
  questions: QuizQuestion[];
}

export interface QuestionResult {
  question_id: number;
  correct: boolean;
  correct_answer: string;
  explanation: string;
}

export interface QuizResult {
  lesson_id: number;
  score: number;
  results: QuestionResult[];
  concept_mastery: { concept_id: number; score: number }[];
}

export interface StudySession {
  id: number;
  material_id: number;
  current_concept_id: number | null;
  status: string;
  created_at: string;
}

export interface NextAction {
  type: "advance" | "practice" | "reteach" | "complete";
  message: string;
  concept: Concept | null;
  lesson: Lesson | null;
  quiz: Quiz | null;
}

export interface User {
  id: number;
  email: string;
  role: string;
  display_name: string;
  grade: number | null;
  language: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface TopicSummary {
  id: number;
  chapter_id: number;
  concept_id: number | null;
  title: string;
  summary: string;
  difficulty: string;
  order_index: number;
}

export interface ChapterSummary {
  id: number;
  subject_id: number;
  title: string;
  order_index: number;
  topics: TopicSummary[];
}

export interface SubjectSummary {
  id: number;
  material_id: number | null;
  name: string;
  language: string;
  order_index: number;
  chapters: ChapterSummary[];
}

export interface Curriculum {
  material_id: number;
  subjects: SubjectSummary[];
}

export interface ReviewSchedule {
  topic_id: number;
  topic_title: string;
  interval_days: number;
  ease: number;
  repetitions: number;
  lapses: number;
  due_at: string | null;
  last_reviewed_at: string | null;
  is_due: boolean;
  mastery: number;
  retention: number;
}

export interface ReviewQueue {
  items: ReviewSchedule[];
  total: number;
}

export interface ReviewSummary {
  due_count: number;
  scheduled_count: number;
  reviewed_count: number;
}

export interface TopicMastery {
  topic_id: number;
  title: string;
  concept_id: number | null;
  mastery: number;
}

export interface MasteryEvent {
  id: number;
  concept_id: number;
  topic_id: number | null;
  score: number;
  delta: number;
  is_correct: boolean;
  source: string;
  created_at: string;
}

export interface TutorMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  grounding: { chunk_id?: number; index?: number; relevance?: number }[];
  created_at: string;
}

export interface TutorConversation {
  id: number;
  topic_id: number | null;
  title: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface TutorConversationSummary extends TutorConversation {
  topic_title: string;
  message_count: number;
}

export interface TutorConversationDetail extends TutorConversation {
  topic_title: string;
  messages: TutorMessage[];
}

export interface TutorReply {
  user_message: TutorMessage;
  reply: TutorMessage;
}

export interface ExamDate {
  id: number;
  subject_id: number | null;
  title: string;
  exam_date: string;
  created_at: string;
}

export interface PlanItem {
  id: number;
  topic_id: number | null;
  topic_title: string;
  scheduled_for: string | null;
  estimated_minutes: number;
  status: "pending" | "done";
  completed_at: string | null;
}

export interface Plan {
  id: number;
  exam_date_id: number | null;
  status: string;
  created_at: string;
}

export interface PlanSummary extends Plan {
  exam_title: string;
  exam_date: string | null;
  total_items: number;
  completed_items: number;
  percent_complete: number;
}

export interface PlanDetail extends PlanSummary {
  items: PlanItem[];
}

export interface Streak {
  current: number;
  longest: number;
  today_count: number;
  last_active_date: string | null;
}

export interface Achievement {
  code: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlocked_at: string | null;
}

export interface ActivePlan {
  id: number;
  total_items: number;
  completed_items: number;
  percent_complete: number;
}

export interface Dashboard {
  streak: Streak;
  topics_total: number;
  topics_covered: number;
  average_mastery: number;
  due_reviews: number;
  achievements_unlocked: number;
  achievements_total: number;
  active_plan: ActivePlan | null;
}

export interface AppNotification {
  id: number;
  type: string;
  title: string;
  body: string;
  read_at: string | null;
  created_at: string;
}

export interface NotificationPage {
  items: AppNotification[];
  unread: number;
}

export interface ProfileUpdate {
  display_name?: string;
  grade?: number | null;
  language?: "en" | "ar";
  timezone?: string;
}

export interface AdminUserPage {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminUserUpdate {
  display_name?: string;
  role?: "student" | "admin" | "teacher" | "parent";
  grade?: number | null;
  is_active?: boolean;
}

export interface AIUsageLog {
  id: number;
  user_id: number | null;
  provider: string;
  model: string;
  operation: string;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
  status: string;
  error: string | null;
  created_at: string;
}

export interface AuditLog {
  id: number;
  actor_user_id: number | null;
  action: string;
  target_type: string;
  target_id: string;
  meta: Record<string, unknown>;
  created_at: string;
}

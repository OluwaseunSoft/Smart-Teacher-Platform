import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type Language = "en" | "ar";

const STORAGE_KEY = "suhail.language";

type Dict = Record<string, string>;

const en: Dict = {
  "nav.dashboard": "Dashboard",
  "nav.library": "Library",
  "nav.tutor": "Tutor",
  "nav.reviews": "Reviews",
  "nav.planner": "Planner",
  "nav.progress": "Progress",
  "nav.notifications": "Notifications",
  "nav.settings": "Settings",
  "nav.admin": "Admin",
  "nav.primary": "Primary navigation",
  "nav.skip": "Skip to content",
  "nav.language": "Language",

  "common.loading": "Loading…",
  "common.error": "Something went wrong",
  "common.save": "Save",
  "common.saving": "Saving…",
  "common.cancel": "Cancel",
  "common.delete": "Delete",
  "common.create": "Create",
  "common.signOut": "Sign out",
  "common.notFound": "Page not found.",
  "common.none": "Nothing here yet.",
  "common.optional": "optional",
  "common.send": "Send",
  "common.close": "Close",
  "common.back": "Back",

  "dashboard.title": "Your dashboard",
  "dashboard.welcome": "Welcome back, {name}",
  "dashboard.subtitle": "Here is where you stand today.",
  "dashboard.streak": "Day streak",
  "dashboard.longest": "Longest {n}",
  "dashboard.topics": "Topics covered",
  "dashboard.mastery": "Average mastery",
  "dashboard.due": "Reviews due",
  "dashboard.achievements": "Achievements",
  "dashboard.plan": "Active plan",
  "dashboard.noPlan": "No active study plan.",
  "dashboard.planProgress": "{done} of {total} tasks · {percent}%",
  "dashboard.startReview": "Start reviewing",
  "dashboard.askTutor": "Ask the tutor",
  "dashboard.makePlan": "Build a study plan",
  "dashboard.explore": "Explore library",

  "onboarding.title": "Welcome to Suhail",
  "onboarding.subtitle": "Tell us a little about yourself to personalize your learning.",
  "onboarding.name": "Your name",
  "onboarding.grade": "Grade",
  "onboarding.language": "Preferred language",
  "onboarding.timezone": "Timezone",
  "onboarding.finish": "Get started",
  "onboarding.gradeOption": "Grade {n}",

  "tutor.title": "Socratic tutor",
  "tutor.subtitle": "Ask questions and get guided, mastery-aware help.",
  "tutor.new": "New conversation",
  "tutor.noConversations": "No conversations yet.",
  "tutor.chooseTopic": "Topic",
  "tutor.general": "General",
  "tutor.start": "Start chatting",
  "tutor.placeholder": "Ask a question…",
  "tutor.thinking": "Thinking…",
  "tutor.empty": "Send the first message to begin.",
  "tutor.delete": "Delete conversation",

  "reviews.title": "Spaced reviews",
  "reviews.subtitle": "Strengthen memory by reviewing at the right time.",
  "reviews.due": "Due now",
  "reviews.scheduled": "Scheduled",
  "reviews.reviewed": "Reviewed",
  "reviews.queueEmpty": "You are all caught up. Nothing due right now.",
  "reviews.dueLabel": "Due {date}",
  "reviews.howWell": "How well did you recall this?",
  "reviews.quality.0": "Nothing",
  "reviews.quality.1": "Hard",
  "reviews.quality.2": "Shaky",
  "reviews.quality.3": "Okay",
  "reviews.quality.4": "Good",
  "reviews.quality.5": "Easy",
  "reviews.interval": "Interval {n}d",
  "reviews.mastery": "Mastery {n}%",

  "planner.title": "Study planner",
  "planner.subtitle": "Plan your revision around upcoming exams.",
  "planner.exams": "Exams",
  "planner.addExam": "Add exam",
  "planner.examTitle": "Exam title",
  "planner.examDate": "Exam date",
  "planner.noExams": "No exams yet.",
  "planner.generate": "Generate plan",
  "planner.dailyMinutes": "Daily minutes",
  "planner.plans": "Plans",
  "planner.noPlans": "No plans yet.",
  "planner.items": "Tasks",
  "planner.markDone": "Mark done",
  "planner.markPending": "Reopen",
  "planner.progress": "{done} of {total} done",
  "planner.minutes": "{n} min",
  "planner.scheduled": "Scheduled {date}",

  "progress.title": "Your progress",
  "progress.subtitle": "Track mastery across every topic.",
  "progress.mastery": "Topic mastery",
  "progress.noMastery": "No topics yet.",
  "progress.achievements": "Achievements",
  "progress.locked": "Locked",
  "progress.unlocked": "Unlocked {date}",
  "progress.history": "Recent activity",

  "notifications.title": "Notifications",
  "notifications.subtitle": "Reminders and milestones.",
  "notifications.markAll": "Mark all as read",
  "notifications.markRead": "Mark as read",
  "notifications.empty": "No notifications.",
  "notifications.unread": "{n} unread",

  "settings.title": "Settings",
  "settings.subtitle": "Manage your profile and preferences.",
  "settings.profile": "Profile",
  "settings.name": "Display name",
  "settings.grade": "Grade",
  "settings.language": "Language",
  "settings.timezone": "Timezone",
  "settings.saved": "Saved.",

  "admin.title": "Admin console",
  "admin.subtitle": "Manage users and monitor AI operations.",
  "admin.forbidden": "You do not have access to this area.",
  "admin.tab.users": "Users",
  "admin.tab.ai": "AI usage",
  "admin.tab.audit": "Audit log",
  "admin.search": "Search by email or name",
  "admin.searchAction": "Search",
  "admin.email": "Email",
  "admin.name": "Name",
  "admin.role": "Role",
  "admin.grade": "Grade",
  "admin.status": "Status",
  "admin.created": "Created",
  "admin.actions": "Actions",
  "admin.active": "Active",
  "admin.inactive": "Inactive",
  "admin.deactivate": "Deactivate",
  "admin.reactivate": "Reactivate",
  "admin.you": "You",
  "admin.empty": "Nothing to show.",
  "admin.total": "{n} users",
  "admin.page": "Page {page} of {pages}",
  "admin.prev": "Previous",
  "admin.next": "Next",
  "admin.provider": "Provider",
  "admin.model": "Model",
  "admin.operation": "Operation",
  "admin.tokens": "Tokens",
  "admin.latency": "Latency",
  "admin.when": "When",
  "admin.actor": "Actor",
  "admin.action": "Action",
  "admin.target": "Target",
  "admin.details": "Details",
  "admin.ms": "{n} ms",
};

const ar: Dict = {
  "nav.dashboard": "لوحة التحكم",
  "nav.library": "المكتبة",
  "nav.tutor": "المعلّم",
  "nav.reviews": "المراجعات",
  "nav.planner": "المخطّط",
  "nav.progress": "التقدّم",
  "nav.notifications": "الإشعارات",
  "nav.settings": "الإعدادات",
  "nav.admin": "الإدارة",
  "nav.primary": "التنقل الرئيسي",
  "nav.skip": "تخطَّ إلى المحتوى",
  "nav.language": "اللغة",

  "common.loading": "جارٍ التحميل…",
  "common.error": "حدث خطأ ما",
  "common.save": "حفظ",
  "common.saving": "جارٍ الحفظ…",
  "common.cancel": "إلغاء",
  "common.delete": "حذف",
  "common.create": "إنشاء",
  "common.signOut": "تسجيل الخروج",
  "common.notFound": "الصفحة غير موجودة.",
  "common.none": "لا يوجد شيء بعد.",
  "common.optional": "اختياري",
  "common.send": "إرسال",
  "common.close": "إغلاق",
  "common.back": "رجوع",

  "dashboard.title": "لوحة التحكم",
  "dashboard.welcome": "مرحبًا بعودتك، {name}",
  "dashboard.subtitle": "إليك وضعك اليوم.",
  "dashboard.streak": "أيام متتالية",
  "dashboard.longest": "الأطول {n}",
  "dashboard.topics": "المواضيع المغطّاة",
  "dashboard.mastery": "متوسط الإتقان",
  "dashboard.due": "مراجعات مستحقة",
  "dashboard.achievements": "الإنجازات",
  "dashboard.plan": "الخطة النشطة",
  "dashboard.noPlan": "لا توجد خطة دراسة نشطة.",
  "dashboard.planProgress": "{done} من {total} مهمة · {percent}%",
  "dashboard.startReview": "ابدأ المراجعة",
  "dashboard.askTutor": "اسأل المعلّم",
  "dashboard.makePlan": "أنشئ خطة دراسة",
  "dashboard.explore": "استكشف المكتبة",

  "onboarding.title": "مرحبًا بك في سُهيل",
  "onboarding.subtitle": "أخبرنا قليلًا عن نفسك لتخصيص تعلّمك.",
  "onboarding.name": "اسمك",
  "onboarding.grade": "الصف",
  "onboarding.language": "اللغة المفضّلة",
  "onboarding.timezone": "المنطقة الزمنية",
  "onboarding.finish": "لنبدأ",
  "onboarding.gradeOption": "الصف {n}",

  "tutor.title": "المعلّم السقراطي",
  "tutor.subtitle": "اطرح الأسئلة واحصل على مساعدة تدرّجية تراعي مستوى إتقانك.",
  "tutor.new": "محادثة جديدة",
  "tutor.noConversations": "لا توجد محادثات بعد.",
  "tutor.chooseTopic": "الموضوع",
  "tutor.general": "عام",
  "tutor.start": "ابدأ الدردشة",
  "tutor.placeholder": "اطرح سؤالًا…",
  "tutor.thinking": "جارٍ التفكير…",
  "tutor.empty": "أرسل الرسالة الأولى للبدء.",
  "tutor.delete": "حذف المحادثة",

  "reviews.title": "المراجعات المتباعدة",
  "reviews.subtitle": "عزّز ذاكرتك بالمراجعة في الوقت المناسب.",
  "reviews.due": "مستحق الآن",
  "reviews.scheduled": "مجدول",
  "reviews.reviewed": "تمت مراجعته",
  "reviews.queueEmpty": "لقد أنجزت كل شيء. لا يوجد مستحق الآن.",
  "reviews.dueLabel": "مستحق {date}",
  "reviews.howWell": "إلى أي مدى تذكّرت هذا؟",
  "reviews.quality.0": "لا شيء",
  "reviews.quality.1": "صعب",
  "reviews.quality.2": "متذبذب",
  "reviews.quality.3": "مقبول",
  "reviews.quality.4": "جيد",
  "reviews.quality.5": "سهل",
  "reviews.interval": "الفترة {n} ي",
  "reviews.mastery": "الإتقان {n}%",

  "planner.title": "مخطّط الدراسة",
  "planner.subtitle": "خطّط مراجعتك حول الاختبارات القادمة.",
  "planner.exams": "الاختبارات",
  "planner.addExam": "إضافة اختبار",
  "planner.examTitle": "عنوان الاختبار",
  "planner.examDate": "تاريخ الاختبار",
  "planner.noExams": "لا توجد اختبارات بعد.",
  "planner.generate": "أنشئ خطة",
  "planner.dailyMinutes": "الدقائق اليومية",
  "planner.plans": "الخطط",
  "planner.noPlans": "لا توجد خطط بعد.",
  "planner.items": "المهام",
  "planner.markDone": "تم",
  "planner.markPending": "أعد الفتح",
  "planner.progress": "{done} من {total} منجزة",
  "planner.minutes": "{n} دقيقة",
  "planner.scheduled": "مجدول {date}",

  "progress.title": "تقدّمك",
  "progress.subtitle": "تابع إتقانك لكل موضوع.",
  "progress.mastery": "إتقان المواضيع",
  "progress.noMastery": "لا توجد مواضيع بعد.",
  "progress.achievements": "الإنجازات",
  "progress.locked": "مقفل",
  "progress.unlocked": "مفتوح {date}",
  "progress.history": "النشاط الأخير",

  "notifications.title": "الإشعارات",
  "notifications.subtitle": "التذكيرات والإنجازات.",
  "notifications.markAll": "تعليم الكل كمقروء",
  "notifications.markRead": "تعليم كمقروء",
  "notifications.empty": "لا توجد إشعارات.",
  "notifications.unread": "{n} غير مقروء",

  "settings.title": "الإعدادات",
  "settings.subtitle": "أدر ملفك الشخصي وتفضيلاتك.",
  "settings.profile": "الملف الشخصي",
  "settings.name": "الاسم المعروض",
  "settings.grade": "الصف",
  "settings.language": "اللغة",
  "settings.timezone": "المنطقة الزمنية",
  "settings.saved": "تم الحفظ.",

  "admin.title": "لوحة الإدارة",
  "admin.subtitle": "أدر المستخدمين وراقب عمليات الذكاء الاصطناعي.",
  "admin.forbidden": "ليس لديك صلاحية الوصول إلى هذه المنطقة.",
  "admin.tab.users": "المستخدمون",
  "admin.tab.ai": "استخدام الذكاء الاصطناعي",
  "admin.tab.audit": "سجل التدقيق",
  "admin.search": "ابحث بالبريد أو الاسم",
  "admin.searchAction": "بحث",
  "admin.email": "البريد الإلكتروني",
  "admin.name": "الاسم",
  "admin.role": "الدور",
  "admin.grade": "الصف",
  "admin.status": "الحالة",
  "admin.created": "أُنشئ",
  "admin.actions": "إجراءات",
  "admin.active": "نشط",
  "admin.inactive": "غير نشط",
  "admin.deactivate": "تعطيل",
  "admin.reactivate": "تفعيل",
  "admin.you": "أنت",
  "admin.empty": "لا يوجد شيء لعرضه.",
  "admin.total": "{n} مستخدم",
  "admin.page": "صفحة {page} من {pages}",
  "admin.prev": "السابق",
  "admin.next": "التالي",
  "admin.provider": "المزوّد",
  "admin.model": "النموذج",
  "admin.operation": "العملية",
  "admin.tokens": "الرموز",
  "admin.latency": "زمن الاستجابة",
  "admin.when": "الوقت",
  "admin.actor": "الفاعل",
  "admin.action": "الإجراء",
  "admin.target": "الهدف",
  "admin.details": "التفاصيل",
  "admin.ms": "{n} م.ث",
};

const DICTS: Record<Language, Dict> = { en, ar };

interface I18nState {
  lang: Language;
  dir: "ltr" | "rtl";
  t: (key: string, vars?: Record<string, string | number>) => string;
  setLanguage: (lang: Language) => void;
}

const I18nContext = createContext<I18nState | null>(null);

function detectInitial(): Language {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "ar") return stored;
  return navigator.language?.toLowerCase().startsWith("ar") ? "ar" : "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Language>(detectInitial);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    localStorage.setItem(STORAGE_KEY, lang);
  }, [lang]);

  const setLanguage = useCallback((next: Language) => setLang(next), []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      let value = DICTS[lang][key] ?? en[key] ?? key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          value = value.replaceAll(`{${k}}`, String(v));
        }
      }
      return value;
    },
    [lang],
  );

  const value = useMemo<I18nState>(
    () => ({ lang, dir: lang === "ar" ? "rtl" : "ltr", t, setLanguage }),
    [lang, t, setLanguage],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nState {
  const ctx = useContext(I18nContext);
  if (ctx === null) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}

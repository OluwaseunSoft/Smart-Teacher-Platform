import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n } from "../i18n";
import { Card, ErrorText, Spinner } from "../components/ui";
import { Icon, type IconName } from "../components/Icon";
import { formatDate } from "../lib/dateTime";

function Stat({ label, value, note, icon, tone }: { label: string; value: string; note: string; icon: IconName; tone: string }) {
  return <Card className={`dashboard-stat ${tone}`}>
    <span className="icon-tile"><Icon name={icon} size={22}/></span>
    <p className="stat-value" dir="ltr">{value}</p><h2>{label}</h2><p className="stat-note">{note}</p>
  </Card>;
}

const percentage = (value: number) => Math.min(100, Math.max(0, Math.round(value * 100)));

export default function DashboardPage() {
  const { user } = useAuth();
  const { t, lang } = useI18n();
  const locale = lang === "ar" ? "ar" : "en";
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: api.getDashboard });
  const today = useQuery({ queryKey: ["study-today"], queryFn: api.getStudyToday });
  if (dashboard.isLoading) return <Spinner label={t("common.loading")}/>;
  if (dashboard.isError) return <ErrorText>{(dashboard.error as Error).message}</ErrorText>;
  const d = dashboard.data!;
  const plan = d.active_plan;
  const next = today.data?.items[0];
  const subjects = d.subject_progress ?? [];
  const trend = (d.score_trend ?? []).slice(-7);
  const exams = d.upcoming_exams ?? [];
  const nextPath = next ? `/topics/${next.topic_id}` : d.topics_total ? "/library" : "/upload";
  const actions: { to: string; title: string; description: string; icon: IconName; tone: string }[] = [
    { to: "/upload", title: "nav.upload", description: "dash.addMaterial", icon: "upload", tone: "tone-blue" },
    { to: "/library", title: "nav.library", description: "dash.openLessons", icon: "book", tone: "tone-teal" },
    { to: "/tutor", title: "dashboard.askTutor", description: "dash.workItOut", icon: "sparkles", tone: "tone-violet" },
    { to: "/planner", title: "nav.planner", description: "dash.makeTime", icon: "calendar", tone: "tone-amber" },
  ];

  return <div className="dashboard-page">
    <section className="dashboard-heading">
      <div><p className="eyebrow">{t("dash.smallSteps")}</p><h1>{t("dashboard.welcome", { name: user?.display_name ?? "" })}<span className="welcome-spark" aria-hidden="true"><Icon name="sparkles" size={25}/></span></h1><p>{t("dash.welcomeSubtitle")}</p></div>
      <span className="study-time-pill"><Icon name="clock" size={17}/>{t("dash.studyTime", { n: d.study_minutes ?? 0 })}</span>
    </section>

    <section className="focus-banner">
      <div className="focus-copy"><span className="focus-label"><span className="live-dot"/>{t("dash.nextStep")}</span>
        <h2>{t("dash.nextWin")}</h2>
        <p>{next ? t("dash.reviewReady", { n: today.data?.items.length ?? 0 }) : d.topics_total ? t("dash.pickTopic") : t("dash.firstUpload")}</p>
        <Link to={nextPath} className="study-button primary">{t(next ? "dash.letsStudy" : d.topics_total ? "dashboard.explore" : "upload.title")}<Icon name="arrow" size={18}/></Link>
      </div>
      <div className="focus-art" aria-hidden="true"><div className="art-orbit orbit-one"/><div className="art-orbit orbit-two"/><span className="art-spark spark-one">✦</span><span className="art-spark spark-two">✧</span><div className="art-book"><Icon name="book" size={66}/></div><span className="art-check"><Icon name="check" size={20}/></span><span className="art-small-star"><Icon name="sparkles" size={24}/></span></div>
    </section>

    <section aria-label={t("dashboard.title")} className="dashboard-stats">
      <Stat label={t("dashboard.streak")} value={String(d.streak.current)} note={t("dashboard.longest", { n: d.streak.longest })} icon="flame" tone="tone-amber"/>
      <Stat label={t("dashboard.topics")} value={`${d.topics_covered} / ${d.topics_total}`} note={t("dash.oneStep")} icon="book" tone="tone-blue"/>
      <Stat label={t("dashboard.mastery")} value={`${percentage(d.average_mastery)}%`} note={t("dash.growingSkills")} icon="target" tone="tone-teal"/>
      <Stat label={t("dashboard.achievements")} value={`${d.achievements_unlocked} / ${d.achievements_total}`} note={t("dash.celebrate")} icon="trophy" tone="tone-violet"/>
    </section>

    <div className="dashboard-columns">
      <div className="dashboard-primary">
        <Card className="today-card">
          <div className="section-heading"><h2><span className="heading-icon tone-blue"><Icon name="review"/></span>{t("dash.studyToday")}</h2><span className="count-pill">{t("dash.dueCount", { n: d.due_reviews })}</span></div>
          <p className="section-description">{t("dash.todayHint")}</p>
          {today.isLoading && <Spinner label={t("common.loading")}/>}
          {today.isError && <ErrorText>{(today.error as Error).message}</ErrorText>}
          {today.data?.items.length === 0 && <div className="friendly-empty"><span className="icon-tile tone-teal"><Icon name="check" size={25}/></span><h3>{t("dash.caughtUp")}</h3><p>{t("dash.caughtUpHint")}</p><Link to="/library" className="text-link">{t("dashboard.explore")}<Icon name="arrow" size={16}/></Link></div>}
          <div className="today-list">{today.data?.items.slice(0, 4).map((item, index) => <Link key={item.topic_id} to={`/topics/${item.topic_id}`} className="study-topic-row">
            <span className={`topic-number ${index % 2 ? "tone-teal" : "tone-blue"}`}>{String(index + 1).padStart(2, "0")}</span><span className="topic-label"><strong dir="auto">{item.title}</strong><small>{t(item.reason === "Review due" ? "dash.readyReview" : "dash.morePractice")}</small></span><Icon name="arrow" size={18}/>
          </Link>)}</div>
          {!!today.data?.items.length && <Link to="/reviews" className="card-footer-link">{t("dash.allReviews")}<Icon name="arrow" size={16}/></Link>}
        </Card>

        <Card>
          <div className="section-heading"><h2><span className="heading-icon tone-teal"><Icon name="chart"/></span>{t("dash.subjects")}</h2><Link to="/progress" className="text-link">{t("dash.viewProgress")}<Icon name="arrow" size={16}/></Link></div>
          {subjects.length === 0 ? <div className="friendly-empty compact"><Icon name="book" size={30}/><p>{t("dash.noSubjects")}</p><Link to="/upload" className="text-link">{t("upload.title")}<Icon name="arrow" size={16}/></Link></div> : <div className="subject-list">{subjects.map((subject, index) => <div key={subject.subject} className={`subject-progress tone-${["blue", "teal", "violet", "amber"][index % 4]}`}>
            <div className="subject-info"><span className="icon-tile"><Icon name="book" size={18}/></span><div><h3 dir="auto">{subject.subject}</h3><p>{t("dash.topicCount", { done: subject.covered, total: subject.total })}</p></div><strong>{percentage(subject.mastery)}%</strong></div>
            <div role="progressbar" aria-label={subject.subject} aria-valuenow={percentage(subject.mastery)} aria-valuemin={0} aria-valuemax={100} className="study-progress-track"><span style={{ width: `${percentage(subject.mastery)}%` }}/></div>
          </div>)}</div>}
        </Card>

        <Card className="plan-card">
          <div className="section-heading"><h2><span className="heading-icon tone-violet"><Icon name="calendar"/></span>{t("dashboard.plan")}</h2></div>
          {plan ? <><p className="section-description">{t("dashboard.planProgress", { done: plan.completed_items, total: plan.total_items, percent: percentage(plan.percent_complete) })}</p><div role="progressbar" aria-label={t("dashboard.plan")} aria-valuenow={Math.min(100, Math.max(0, percentage(plan.percent_complete)))} aria-valuemin={0} aria-valuemax={100} className="study-progress-track tone-violet"><span style={{ width: `${percentage(plan.percent_complete)}%` }}/></div></> : <p className="section-description">{t("dash.planHint")}</p>}
          <Link to="/planner" className="study-button secondary">{t("dashboard.makePlan")}<Icon name="arrow" size={16}/></Link>
        </Card>
      </div>

      <div className="dashboard-secondary">
        <Card><div className="section-heading"><h2><span className="heading-icon tone-amber"><Icon name="sparkles"/></span>{t("dash.quickActions")}</h2></div><div className="quick-actions">{actions.map(action => <Link key={action.to} to={action.to} className="quick-action"><span className={`icon-tile ${action.tone}`}><Icon name={action.icon}/></span><span><strong>{t(action.title)}</strong><small>{t(action.description)}</small></span><Icon name="arrow" size={16}/></Link>)}</div></Card>
        <Card><div className="section-heading"><h2><span className="heading-icon tone-teal"><Icon name="chart"/></span>{t("dash.scoreTrend")}</h2><span className="mini-label">{t("dash.lastSeven")}</span></div>
          {trend.length === 0 ? <div className="friendly-empty compact"><Icon name="chart" size={30}/><p>{t("dash.noScores")}</p><Link to="/library" className="text-link">{t("dash.findQuiz")}<Icon name="arrow" size={16}/></Link></div> : <div className="score-chart">{trend.map(point => <div className="score-column" key={point.date}><span className="score-value">{percentage(point.score)}%</span><div className="score-bar-track"><div className="score-bar" style={{ height: `${percentage(point.score)}%` }}/></div><time dateTime={point.date} title={formatDate(point.date, user?.timezone ?? "Asia/Dubai", locale)}>{new Intl.DateTimeFormat(locale, { weekday: "short", timeZone: "UTC" }).format(new Date(`${point.date}T12:00:00Z`))}</time><span className="sr-only">{t("dash.answers", { n: point.attempts })}</span></div>)}</div>}
          <p className="chart-caption">{t("dash.progressPace")}</p>
        </Card>
        <Card><div className="section-heading"><h2><span className="heading-icon tone-violet"><Icon name="calendar"/></span>{t("dash.exams")}</h2></div>{exams.length === 0 ? <p className="section-description">{t("dash.noExams")}</p> : <div className="exam-list">{exams.slice(0, 3).map(exam => <Link to="/planner" key={exam.id} className="exam-row"><span className="icon-tile tone-violet"><Icon name="calendar" size={18}/></span><span><strong dir="auto">{exam.title}</strong><time dateTime={exam.exam_date}>{formatDate(exam.exam_date, user?.timezone ?? "Asia/Dubai", locale)}</time></span></Link>)}</div>}<Link to="/planner" className="text-link">{t("dash.planAhead")}<Icon name="arrow" size={16}/></Link></Card>
      </div>
    </div>
  </div>;
}

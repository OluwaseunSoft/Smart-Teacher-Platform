import { Link } from "react-router-dom";

const features = [
  "Upload PDFs, notes, and text",
  "Turn study material into structured lessons",
  "Practice with adaptive quizzes and spaced reviews",
  "Ask a Socratic tutor grounded in your own content",
  "Track study streaks, mastery, and upcoming exams",
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-10 lg:py-16">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-500 text-lg font-bold text-white">
              S
            </span>
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-indigo-200">
                Suhail
              </p>
              <p className="text-xs text-slate-300">Smart Teacher Platform</p>
            </div>
          </div>

          <nav aria-label="Landing page navigation" className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-100 transition hover:border-indigo-400 hover:text-white"
            >
              Sign in
            </Link>
            <Link
              to="/login"
              state={{ mode: "signup" }}
              className="rounded-lg bg-indigo-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-400"
            >
              Create account
            </Link>
          </nav>
        </header>

        <section className="grid items-center gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6">
            <p className="inline-flex rounded-full border border-indigo-400/40 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-200">
              AI-powered adaptive learning for students
            </p>
            <h1 className="max-w-xl text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Learn with a tutor that understands your material.
            </h1>
            <p className="max-w-xl text-base text-slate-300 sm:text-lg">
              Suhail reads study notes, structures them by topic, generates grounded
              explanations, and creates adaptive quizzes and review plans that help
              students improve over time.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <Link
                to="/login"
                state={{ mode: "signup" }}
                className="rounded-xl bg-indigo-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400"
              >
                Start learning
              </Link>
              <Link
                to="/login"
                className="rounded-xl border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-100 transition hover:border-slate-500 hover:bg-slate-900"
              >
                I already have an account
              </Link>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl shadow-indigo-950/30">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">What students get</h2>
                <span className="rounded-full bg-emerald-500/15 px-2 py-1 text-xs font-medium text-emerald-300">
                  Core MVP
                </span>
              </div>
              <ul className="space-y-3 text-sm text-slate-200">
                {features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <span className="mt-0.5 inline-block h-2.5 w-2.5 rounded-full bg-indigo-400" aria-hidden="true" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

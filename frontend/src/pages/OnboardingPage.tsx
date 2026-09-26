import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n, type Language } from "../i18n";
import { markOnboarded } from "../lib/onboarding";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

const GRADES = Array.from({ length: 12 }, (_, i) => i + 1);

export default function OnboardingPage() {
  const { user, refresh } = useAuth();
  const { t, setLanguage } = useI18n();
  const navigate = useNavigate();

  const [name, setName] = useState(user?.display_name ?? "");
  const [grade, setGrade] = useState<number | "">(user?.grade ?? "");
  const [language, setLocalLanguage] = useState<Language>(
    (user?.language as Language) ?? "en",
  );
  const [timezone, setTimezone] = useState(
    user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.updateProfile({
        display_name: name.trim() || undefined,
        grade: grade === "" ? null : grade,
        language,
        timezone: timezone.trim() || undefined,
      });
      setLanguage(language);
      await refresh();
      if (user) markOnboarded(user.id);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-slate-50 px-6">
      <Card className="w-full max-w-lg space-y-5">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold">{t("onboarding.title")}</h1>
          <p className="text-sm text-slate-500">{t("onboarding.subtitle")}</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="ob-name"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("onboarding.name")}
            </label>
            <input
              id="ob-name"
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label
              htmlFor="ob-grade"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("onboarding.grade")}
            </label>
            <select
              id="ob-grade"
              value={grade}
              onChange={(e) =>
                setGrade(e.target.value === "" ? "" : Number(e.target.value))
              }
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            >
              <option value="">—</option>
              {GRADES.map((g) => (
                <option key={g} value={g}>
                  {t("onboarding.gradeOption", { n: g })}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="ob-language"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("onboarding.language")}
            </label>
            <select
              id="ob-language"
              value={language}
              onChange={(e) => setLocalLanguage(e.target.value as Language)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            >
              <option value="en">English</option>
              <option value="ar">العربية</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="ob-timezone"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("onboarding.timezone")}
            </label>
            <input
              id="ob-timezone"
              autoComplete="off"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <ErrorText>{error}</ErrorText>

          <Button type="submit" disabled={busy} className="w-full">
            {busy ? (
              <span className="flex justify-center">
                <Spinner />
              </span>
            ) : (
              t("onboarding.finish")
            )}
          </Button>
        </form>
      </Card>
    </div>
  );
}

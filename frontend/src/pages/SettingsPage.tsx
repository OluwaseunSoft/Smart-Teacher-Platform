import { useState, type FormEvent } from "react";

import { api } from "../api/client";
import { useAuth } from "../auth";
import { useI18n, type Language } from "../i18n";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

const GRADES = Array.from({ length: 12 }, (_, i) => i + 1);

export default function SettingsPage() {
  const { user, refresh } = useAuth();
  const { t, setLanguage } = useI18n();

  const [name, setName] = useState(user?.display_name ?? "");
  const [grade, setGrade] = useState<number | "">(user?.grade ?? "");
  const [language, setLocalLanguage] = useState<Language>(
    (user?.language as Language) ?? "en",
  );
  const [timezone, setTimezone] = useState(user?.timezone ?? "");
  const [privacy, setPrivacy] = useState({
    analytics: true,
    reminders: true,
    personalizedAI: true,
  });
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
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
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.error"));
    } finally {
      setBusy(false);
    }
  }

  const exportData = () => {
    const payload = {
      display_name: name,
      grade,
      language,
      timezone,
      privacy,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "suhail-data-export.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const deleteData = () => {
    if (!window.confirm("This will permanently clear your local profile data. Continue?")) {
      return;
    }
    setName("");
    setGrade("");
    setTimezone("");
    setSaved(true);
  };

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <section className="space-y-1">
        <h1 className="text-2xl font-semibold">{t("settings.title")}</h1>
        <p className="text-slate-600">{t("settings.subtitle")}</p>
      </section>

      <Card className="space-y-4">
        <h2 className="text-lg font-semibold">{t("settings.profile")}</h2>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="set-name"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("settings.name")}
            </label>
            <input
              id="set-name"
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label
              htmlFor="set-grade"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("settings.grade")}
            </label>
            <select
              id="set-grade"
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
              htmlFor="set-language"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("settings.language")}
            </label>
            <select
              id="set-language"
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
              htmlFor="set-timezone"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              {t("settings.timezone")}
            </label>
            <input
              id="set-timezone"
              autoComplete="off"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <fieldset className="space-y-3">
            <legend className="text-sm font-medium text-slate-700">Privacy controls</legend>
            <label className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600">
              <span>Allow analytics</span>
              <input
                type="checkbox"
                checked={privacy.analytics}
                onChange={(e) =>
                  setPrivacy((prev) => ({ ...prev, analytics: e.target.checked }))
                }
              />
            </label>
            <label className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600">
              <span>Personalized reminders</span>
              <input
                type="checkbox"
                checked={privacy.reminders}
                onChange={(e) =>
                  setPrivacy((prev) => ({ ...prev, reminders: e.target.checked }))
                }
              />
            </label>
            <label className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600">
              <span>Use my data for AI personalization</span>
              <input
                type="checkbox"
                checked={privacy.personalizedAI}
                onChange={(e) =>
                  setPrivacy((prev) => ({ ...prev, personalizedAI: e.target.checked }))
                }
              />
            </label>
          </fieldset>

          <ErrorText>{error}</ErrorText>
          {saved && <p className="text-sm text-emerald-600">{t("settings.saved")}</p>}

          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={busy}>
              {busy ? (
                <span className="flex items-center gap-2">
                  <Spinner />
                  {t("common.saving")}
                </span>
              ) : (
                t("common.save")
              )}
            </Button>
            <Button type="button" variant="secondary" onClick={exportData}>
              Export data
            </Button>
            <Button type="button" variant="secondary" onClick={deleteData}>
              Delete data
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

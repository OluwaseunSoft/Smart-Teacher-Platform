import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

export default function ResetPasswordPage() {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState<"request" | "confirm">("request");

  async function handleRequest(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);
    try {
      const result = await api.requestPasswordReset(email.trim());
      setMessage(result.detail);
      setStep("confirm");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send reset link.");
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);
    try {
      const result = await api.confirmPasswordReset(token.trim(), newPassword);
      setMessage(result.detail || "Password updated successfully.");
      setToken("");
      setNewPassword("");
      setStep("request");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reset password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-slate-50 px-4 py-8">
      <Card className="w-full max-w-md space-y-4">
        <div className="text-center">
          <span className="mx-auto grid h-10 w-10 place-items-center rounded-lg bg-indigo-600 text-lg font-bold text-white">
            S
          </span>
          <h1 className="mt-3 text-xl font-semibold">Reset password</h1>
          <p className="text-sm text-slate-500">
            {step === "request"
              ? "Enter your email to get a reset code."
              : "Use the reset token and choose a new password."}
          </p>
        </div>

        {step === "request" ? (
          <form onSubmit={handleRequest} className="space-y-4">
            <div>
              <label htmlFor="reset-email" className="mb-1 block text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                id="reset-email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                placeholder="you@example.com"
              />
            </div>
            <ErrorText>{error}</ErrorText>
            {message && <p className="text-sm text-emerald-600">{message}</p>}
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? <span className="flex justify-center"><Spinner /></span> : "Send reset link"}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleConfirm} className="space-y-4">
            <div>
              <label htmlFor="reset-token" className="mb-1 block text-sm font-medium text-slate-700">
                Reset token
              </label>
              <input
                id="reset-token"
                type="text"
                required
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                placeholder="Paste the reset token"
              />
            </div>
            <div>
              <label htmlFor="reset-password" className="mb-1 block text-sm font-medium text-slate-700">
                New password
              </label>
              <input
                id="reset-password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                placeholder="At least 8 characters"
              />
            </div>
            <ErrorText>{error}</ErrorText>
            {message && <p className="text-sm text-emerald-600">{message}</p>}
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? <span className="flex justify-center"><Spinner /></span> : "Update password"}
            </Button>
          </form>
        )}

        <div className="flex items-center justify-between text-sm">
          <Link to="/login" className="font-medium text-indigo-600 hover:underline">
            Back to sign in
          </Link>
          <button
            type="button"
            className="font-medium text-slate-600 hover:underline"
            onClick={() => {
              setStep("request");
              setMessage("");
              setError("");
            }}
          >
            Request again
          </button>
        </div>
      </Card>
    </div>
  );
}

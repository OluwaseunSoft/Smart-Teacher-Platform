import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../auth";
import { Button, Card, ErrorText, Spinner } from "../components/ui";

export default function LoginPage() {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const isSignup = mode === "signup";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isSignup) {
        await signup(email, password, displayName || email.split("@")[0]);
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-slate-50 px-6">
      <Card className="w-full max-w-md">
        <div className="mb-6 text-center">
          <span className="mx-auto grid h-10 w-10 place-items-center rounded-lg bg-indigo-600 text-lg font-bold text-white">
            S
          </span>
          <h1 className="mt-3 text-xl font-semibold">Suhail Smart Teacher</h1>
          <p className="text-sm text-slate-500">
            {isSignup ? "Create your account" : "Sign in to continue"}
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          {isSignup && (
            <div>
              <label
                htmlFor="login-name"
                className="mb-1 block text-sm font-medium text-slate-700"
              >
                Name
              </label>
              <input
                id="login-name"
                type="text"
                autoComplete="name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                placeholder="Ada Lovelace"
              />
            </div>
          )}
          <div>
            <label
              htmlFor="login-email"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Email
            </label>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label
              htmlFor="login-password"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Password
            </label>
            <input
              id="login-password"
              type="password"
              required
              minLength={8}
              autoComplete={isSignup ? "new-password" : "current-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
              placeholder="At least 8 characters"
            />
          </div>

          <ErrorText>{error}</ErrorText>

          <Button type="submit" disabled={busy} className="w-full">
            {busy ? (
              <span className="flex justify-center">
                <Spinner />
              </span>
            ) : isSignup ? (
              "Create account"
            ) : (
              "Sign in"
            )}
          </Button>
        </form>

        <div className="mt-4 space-y-3 text-center text-sm text-slate-500">
          {!isSignup && (
            <div>
              <Link to="/reset-password" className="font-medium text-indigo-600 hover:underline">
                Forgot password?
              </Link>
            </div>
          )}
          <p>
            {isSignup ? "Already have an account?" : "New here?"}{" "}
            <button
              type="button"
              onClick={() => {
                setMode(isSignup ? "login" : "signup");
                setError("");
              }}
              className="font-medium text-indigo-600 hover:underline"
            >
              {isSignup ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>
      </Card>
    </div>
  );
}

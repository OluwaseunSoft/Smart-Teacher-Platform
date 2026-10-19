import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`study-card rounded-2xl border border-slate-200 bg-white p-5 ${className}`}
    >
      {children}
    </div>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonProps) {
  const styles: Record<string, string> = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50",
    secondary:
      "border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 disabled:opacity-50",
    ghost: "text-indigo-600 hover:bg-indigo-50 disabled:opacity-50",
  };
  return (
    <button
      className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed ${styles[variant]} ${className}`}
      {...props}
    />
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label ?? "Loading"}
      className="flex items-center gap-2 text-slate-500"
    >
      <span
        aria-hidden="true"
        className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"
      />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}

export function ErrorText({ children }: { children: ReactNode }) {
  if (!children) return null;
  return (
    <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
      {children}
    </p>
  );
}

const STATUS_STYLES: Record<string, string> = {
  uploaded: "bg-slate-100 text-slate-600",
  processing: "bg-amber-100 text-amber-700",
  ready: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  intro: "bg-sky-100 text-sky-700",
  core: "bg-indigo-100 text-indigo-700",
  advanced: "bg-purple-100 text-purple-700",
};

export function Badge({ value }: { value: string }) {
  const style = STATUS_STYLES[value] ?? "bg-slate-100 text-slate-600";
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {value}
    </span>
  );
}

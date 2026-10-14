export function parseTimestamp(value: string): Date {
  const hasZone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value);
  return new Date(hasZone ? value : `${value}Z`);
}

export function formatTimestamp(
  value: string,
  timeZone: string,
  locale: string,
): string {
  try {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone,
    }).format(parseTimestamp(value));
  } catch {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Dubai",
    }).format(parseTimestamp(value));
  }
}

export function formatDate(
  value: string,
  timeZone: string,
  locale: string,
): string {
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(value);
  const date = dateOnly
    ? new Date(`${value}T12:00:00Z`)
    : parseTimestamp(value);
  try {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeZone: dateOnly ? "UTC" : timeZone,
    }).format(date);
  } catch {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeZone: "Asia/Dubai",
    }).format(date);
  }
}


export function formatCurrency(value: unknown, currency = "INR", locale = "en-IN"): string {
  if (value == null || (typeof value === "string" && value.trim() === "")) return "Undisclosed";
  const amount = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(amount)) return "Undisclosed";
  try {
    return new Intl.NumberFormat(locale, { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
  } catch {
    return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(amount);
  }
}

export function formatSalaryRange(min?: number | null, max?: number | null, currency = "INR", locale = "en-IN"): string {
  if (min == null && max == null) return "Undisclosed";
  if (min != null && max != null) return `${formatCurrency(min, currency, locale)}–${formatCurrency(max, currency, locale)}`;
  if (min != null) return `${formatCurrency(min, currency, locale)}+`;
  return `Up to ${formatCurrency(max, currency, locale)}`;
}

export function formatDateTime(value: string | Date | null | undefined, locale = "en-IN", timeZone?: string): string {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short", timeZone }).format(date);
}

export function formatRelativeTime(value: string | Date | null | undefined, locale = "en-IN"): string {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const diff = date.getTime() - Date.now();
  const abs = Math.abs(diff);
  const unit = abs < 60_000 ? "second" : abs < 3_600_000 ? "minute" : abs < 86_400_000 ? "hour" : "day";
  const div = unit === "second" ? 1000 : unit === "minute" ? 60_000 : unit === "hour" ? 3_600_000 : 86_400_000;
  return new Intl.RelativeTimeFormat(locale, { numeric: "auto" }).format(Math.round(diff / div), unit);
}

export function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}


import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes safely */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format an ISO duration in minutes to "Xh Ym" */
export function formatDuration(minutes: number | null | undefined): string {
  if (!minutes) return "N/A";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

/** Format a price level (0-4) to dollar-sign string */
export function formatPriceLevel(level: number | null | undefined): string {
  if (level === null || level === undefined) return "N/A";
  return "$".repeat(Math.max(1, level + 1));
}

/** Return star emoji string from numeric rating */
export function formatRating(rating: number | null | undefined): string {
  if (!rating) return "No rating";
  return `${rating.toFixed(1)} ★`;
}

/** Truncate a string with ellipsis */
export function truncate(str: string, max = 120): string {
  return str.length <= max ? str : str.slice(0, max) + "…";
}

/** Generate a random UUID v4 (client-side session ID) */
export function uuid(): string {
  return crypto.randomUUID();
}

/** Convert a YYYY-MM-DD string to a human-readable date */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

/** Convert a relative ms duration to a human-readable string */
export function formatElapsed(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}m ${rem}s`;
}

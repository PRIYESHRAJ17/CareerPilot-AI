export type Locale = "en-IN" | "en-US";
export const LOCALES: Locale[] = ["en-IN", "en-US"];
export function getLocale(): Locale { if (typeof window === "undefined") return "en-IN"; const raw = localStorage.getItem("careerpilot.locale"); return LOCALES.includes(raw as Locale) ? raw as Locale : (navigator.language.startsWith("en-US") ? "en-US" : "en-IN"); }
export const messages = { "en-IN": { save: "Save", cancel: "Cancel", loading: "Loading", undisclosed: "Undisclosed" }, "en-US": { save: "Save", cancel: "Cancel", loading: "Loading", undisclosed: "Undisclosed" } } as const;

import { getPreferredUiLocale, setStoredUiLocale } from "./uiLocale.ts";

const RTL_LANGUAGE_CODES = new Set([
    "ar",
    "fa",
    "he",
    "ur",
]);

export function normalizeLocaleTag(locale: string): string {
    return locale.trim().replace(/_/g, "-");
}

export function getActiveUiLocale(): string {
    return normalizeLocaleTag(getPreferredUiLocale());
}

export function persistActiveUiLocale(locale: string): string {
    return normalizeLocaleTag(setStoredUiLocale(locale)) || "en";
}

export function isRtlLocale(locale: string): boolean {
    const normalized = normalizeLocaleTag(locale).toLowerCase();
    if (!normalized) return false;
    const language = normalized.split("-", 1)[0];
    return RTL_LANGUAGE_CODES.has(language);
}

export function applyDocumentLocaleDirection(locale: string): void {
    const normalized = normalizeLocaleTag(locale) || "en";
    document.documentElement.lang = normalized;
    document.documentElement.dir = isRtlLocale(normalized) ? "rtl" : "ltr";
}

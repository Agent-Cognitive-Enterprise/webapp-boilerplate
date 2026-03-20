import { normalizeLocale } from "./setupWizardLocales.ts";

function canonicalizeUiLocale(locale: string): string | null {
    const normalized = normalizeLocale(locale);
    if (!normalized) {
        return null;
    }
    return normalized.split("-", 1)[0].toLowerCase();
}

export function getStoredUiLocale(): string | null {
    const stored = localStorage.getItem("uiLocale");
    if (!stored) {
        return null;
    }
    return canonicalizeUiLocale(stored);
}

export function getNavigatorUiLocale(): string {
    return canonicalizeUiLocale(navigator.language || "en") || "en";
}

export function getPreferredUiLocale(localeOverride?: string): string {
    return (
        canonicalizeUiLocale(localeOverride || "") ||
        getStoredUiLocale() ||
        getNavigatorUiLocale()
    );
}

export function setStoredUiLocale(locale: string): string {
    const normalized = canonicalizeUiLocale(locale) || "en";
    localStorage.setItem("uiLocale", normalized);
    return normalized;
}

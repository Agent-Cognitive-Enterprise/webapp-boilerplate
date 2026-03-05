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
    return normalizeLocaleTag(
        localStorage.getItem("uiLocale") || navigator.language || "en",
    );
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

export const SETUP_SUPPORTED_LOCALES = [
    "en",
    "es",
    "fr",
    "de",
    "pt-BR",
    "zh-CN",
    "ja",
    "ko",
    "ar",
    "hi",
    "ru",
] as const;

export type SetupLocale = typeof SETUP_SUPPORTED_LOCALES[number];

export function normalizeLocale(locale: string): string {
    return locale.trim().replace(/_/g, "-");
}

export function resolveSetupLocale(input: string): SetupLocale | null {
    const normalized = normalizeLocale(input);
    if (!normalized) {
        return null;
    }

    if (SETUP_SUPPORTED_LOCALES.includes(normalized as SetupLocale)) {
        return normalized as SetupLocale;
    }

    const language = normalized.toLowerCase().split("-", 1)[0];
    const matched = SETUP_SUPPORTED_LOCALES.find(
        (loc) => loc.toLowerCase() === language || loc.toLowerCase().split("-", 1)[0] === language,
    );

    return matched ?? null;
}

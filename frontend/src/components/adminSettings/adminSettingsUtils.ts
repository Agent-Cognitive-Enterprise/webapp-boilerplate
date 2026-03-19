import {normalizeLocale} from "../../i18n/setupWizardLocales.ts";

export const EXISTING_SECRET_PLACEHOLDER = "********";

export async function fileToDataUrl(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(new Error("Failed to read file"));
        reader.readAsDataURL(file);
    });
}

export function parseSupportedLocales(raw: string): string[] {
    const normalized: string[] = [];
    for (const locale of raw.split(",")) {
        const value = normalizeLocale(locale);
        if (!value) continue;
        if (!normalized.includes(value)) normalized.push(value);
    }
    return normalized;
}

export function resolveAdminSettingsLocale(): string {
    return normalizeLocale(localStorage.getItem("uiLocale") || navigator.language?.slice(0, 2) || "en") || "en";
}

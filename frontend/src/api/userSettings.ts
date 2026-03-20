// /frontend/src/api/userSettings.ts

import api from "./api";
import { normalizeLocaleTag } from "../i18n/localeDirection.ts";

const BASE = "/user-settings";
export const UI_LOCALE_SETTINGS_ROUTE = "/preferences/ui-locale";

export interface UserSettings {
    route: string;
    settings: Record<string, unknown> | null;
    user_id: string;
}

// Get settings for a route
export async function getUserSettings(route: string): Promise<UserSettings | null> {
    try {
        const response = await api.post<UserSettings>(BASE, {
            route,
            settings: null,
        });
        return response.data ?? null;
    } catch {
        return null;
    }
}

// Upsert / save settings for a route
export async function setUserSettings(
    route: string,
    settings: Record<string, unknown>,
): Promise<UserSettings | null> {
    try {
        const response = await api.post<UserSettings>(BASE, {
            route,
            settings,
        });
        return response.data ?? null;
    } catch {
        return null;
    }
}

export async function getSavedUiLocalePreference(): Promise<string | null> {
    const settings = await getUserSettings(UI_LOCALE_SETTINGS_ROUTE);
    const locale = settings?.settings?.locale;
    if (typeof locale !== "string" || locale.trim() === "") {
        return null;
    }
    return normalizeLocaleTag(locale);
}

export async function setSavedUiLocalePreference(locale: string): Promise<string | null> {
    const normalized = normalizeLocaleTag(locale);
    if (!normalized) {
        return null;
    }

    const response = await setUserSettings(UI_LOCALE_SETTINGS_ROUTE, { locale: normalized });
    return typeof response?.settings?.locale === "string" ? normalized : null;
}

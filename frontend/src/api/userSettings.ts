// /frontend/src/api/userSettings.ts

import api from "./api";

const BASE = "/user-settings";

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

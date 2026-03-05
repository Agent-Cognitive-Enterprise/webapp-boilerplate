import api from "./api";

type HealthResponse = {
    app_name?: unknown;
    site_logo?: unknown;
    background_image?: unknown;
};

const FALLBACK_APP_NAME = "webapp-boilerplate";

export async function fetchAppName(): Promise<string> {
    const response = await api.get<HealthResponse>("/health");
    const appName = response.data?.app_name;
    if (typeof appName === "string" && appName.trim().length > 0) {
        return appName.trim();
    }
    return FALLBACK_APP_NAME;
}

export type PublicBranding = {
    appName: string;
    siteLogo: string | null;
    backgroundImage: string | null;
};

export async function fetchPublicBranding(): Promise<PublicBranding> {
    const response = await api.get<HealthResponse>("/health");
    const appName =
        typeof response.data?.app_name === "string" && response.data.app_name.trim().length > 0
            ? response.data.app_name.trim()
            : FALLBACK_APP_NAME;
    const siteLogo =
        typeof response.data?.site_logo === "string" && response.data.site_logo.trim().length > 0
            ? response.data.site_logo
            : null;
    const backgroundImage =
        typeof response.data?.background_image === "string" && response.data.background_image.trim().length > 0
            ? response.data.background_image
            : null;

    return { appName, siteLogo, backgroundImage };
}

export async function initializeDocumentTitle(): Promise<void> {
    try {
        document.title = await fetchAppName();
    } catch {
        document.title = FALLBACK_APP_NAME;
    }
}

import api from "./api";

export type AdminSettings = {
    site_name: string | null;
    default_locale: string | null;
    supported_locales: string[];
    site_logo: string | null;
    background_image: string | null;
    openai_api_key_masked: string | null;
    deepseek_api_key_masked: string | null;
    admin_email: string;
    smtp_host: string | null;
    smtp_port: number | null;
    smtp_username: string | null;
    smtp_password_masked: string | null;
    smtp_from_email: string | null;
    smtp_use_tls: boolean;
    auth_frontend_base_url: string | null;
    auth_backend_base_url: string | null;
    email_configured: boolean;
};

export type AdminSettingsUpdatePayload = {
    site_name?: string;
    default_locale?: string;
    supported_locales?: string[];
    site_logo?: string | null;
    background_image?: string | null;
    openai_api_key?: string | null;
    deepseek_api_key?: string | null;
    admin_email?: string;
    admin_password?: string;
    smtp_host?: string | null;
    smtp_port?: number | null;
    smtp_username?: string | null;
    smtp_password?: string | null;
    smtp_from_email?: string | null;
    smtp_use_tls?: boolean;
    auth_frontend_base_url?: string | null;
    auth_backend_base_url?: string | null;
};

export type EmailSettingsCheckPayload = {
    smtp_host?: string;
    smtp_port?: number;
    smtp_username?: string;
    smtp_password?: string;
    smtp_from_email?: string;
    smtp_use_tls?: boolean;
};

export async function getAdminSettings(): Promise<AdminSettings> {
    const response = await api.get<AdminSettings>("/admin/settings");
    return response.data;
}

export async function updateAdminSettings(
    payload: AdminSettingsUpdatePayload,
): Promise<AdminSettings> {
    const response = await api.put<AdminSettings>("/admin/settings", payload);
    return response.data;
}

export async function checkAdminEmailSettings(
    payload: EmailSettingsCheckPayload,
): Promise<{ success: boolean; message: string }> {
    const response = await api.post("/admin/settings/email/check", payload);
    return response.data;
}

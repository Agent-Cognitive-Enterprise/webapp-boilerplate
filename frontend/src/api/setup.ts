import api from "./api";

export type SetupStatus = {
    is_initialized: boolean;
    site_name?: string | null;
    initialized_at?: string | null;
    seed_locales?: string[];
    email_defaults?: {
        smtp_host?: string | null;
        smtp_port?: number | null;
        smtp_username?: string | null;
        smtp_password?: string | null;
        smtp_from_email?: string | null;
        smtp_use_tls?: boolean;
        auth_frontend_base_url?: string | null;
        auth_backend_base_url?: string | null;
    } | null;
};

export type SetupPayload = {
    setup_token: string;
    site_name: string;
    default_locale: string;
    supported_locales: string[];
    admin_email: string;
    admin_password: string;
    smtp_host?: string;
    smtp_port?: number;
    smtp_username?: string;
    smtp_password?: string;
    smtp_from_email?: string;
    smtp_use_tls?: boolean;
    auth_frontend_base_url?: string;
    auth_backend_base_url?: string;
};

export type EmailSettingsCheckPayload = {
    smtp_host?: string;
    smtp_port?: number;
    smtp_username?: string;
    smtp_password?: string;
    smtp_from_email?: string;
    smtp_use_tls?: boolean;
};

export async function getSetupStatus(): Promise<SetupStatus> {
    const response = await api.get<SetupStatus>("/setup/status");
    return response.data;
}

export async function runSetup(payload: SetupPayload) {
    return api.post("/setup", payload);
}

export async function checkSetupEmailSettings(payload: EmailSettingsCheckPayload) {
    const response = await api.post("/setup/email/check", payload);
    return response.data;
}

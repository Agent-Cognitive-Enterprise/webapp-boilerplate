export type SetupEmailDefaults = {
    smtp_host?: string | null;
    smtp_port?: number | null;
    smtp_username?: string | null;
    smtp_password?: string | null;
    smtp_from_email?: string | null;
    smtp_use_tls?: boolean;
    auth_frontend_base_url?: string | null;
    auth_backend_base_url?: string | null;
} | null;

export type FieldErrors = {
    setup_token?: string;
    site_name?: string;
    supported_locales?: string;
    admin_email?: string;
    admin_password?: string;
    smtp_host?: string;
    smtp_port?: string;
    smtp_from_email?: string;
};

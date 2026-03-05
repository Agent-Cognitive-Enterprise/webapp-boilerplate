import React, {useEffect, useMemo, useState} from "react";
import {Link, useNavigate} from "react-router-dom";
import {checkSetupEmailSettings, runSetup} from "../api/setup";
import {
    getSetupCopy,
    normalizeLocale,
    resolveSetupLocale,
} from "../i18n/setupWizardLocales";

type SetupWizardProps = {
    isInitialized: boolean;
    onSetupComplete: () => void;
    seedLocales: string[];
    emailDefaults?: {
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

type FieldErrors = {
    setup_token?: string;
    site_name?: string;
    supported_locales?: string;
    admin_email?: string;
    admin_password?: string;
    smtp_host?: string;
    smtp_port?: string;
    smtp_from_email?: string;
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function resolveBrowserLocale(availableLocales: string[]): string {
    const fallback = availableLocales.includes("en") ? "en" : (availableLocales[0] ?? "en");
    const browserLocale = normalizeLocale(navigator.language || "en");
    if (!browserLocale) {
        return fallback;
    }
    if (availableLocales.includes(browserLocale)) {
        return browserLocale;
    }
    const browserLanguage = browserLocale.toLowerCase().split("-", 1)[0];
    const matched = availableLocales.find((locale) => (
        normalizeLocale(locale).toLowerCase().split("-", 1)[0] === browserLanguage
    ));
    return matched ?? fallback;
}

function parseLocales(raw: string): string[] {
    const normalized: string[] = [];
    for (const locale of raw.split(",")) {
        const value = normalizeLocale(locale);
        if (!value) {
            continue;
        }
        if (!normalized.includes(value)) {
            normalized.push(value);
        }
    }
    return normalized;
}

export default function SetupWizard({isInitialized, onSetupComplete, seedLocales, emailDefaults}: SetupWizardProps) {
    const navigate = useNavigate();
    const normalizedSeedLocales = useMemo(
        () => parseLocales((seedLocales ?? []).join(",")),
        [seedLocales],
    );
    const initialLocale = useMemo(
        () => resolveBrowserLocale(normalizedSeedLocales),
        [normalizedSeedLocales],
    );

    const [setupToken, setSetupToken] = useState("");
    const [siteName, setSiteName] = useState("");
    const [defaultLocale, setDefaultLocale] = useState(initialLocale);
    const [supportedLocalesRaw, setSupportedLocalesRaw] = useState(normalizedSeedLocales.join(", "));
    const [adminEmail, setAdminEmail] = useState("");
    const [adminPassword, setAdminPassword] = useState("");
    const [smtpHost, setSmtpHost] = useState(() => emailDefaults?.smtp_host ?? "");
    const [smtpPort, setSmtpPort] = useState(() => emailDefaults?.smtp_port != null ? String(emailDefaults.smtp_port) : "");
    const [smtpUsername, setSmtpUsername] = useState(() => emailDefaults?.smtp_username ?? "");
    const [smtpPassword, setSmtpPassword] = useState(() => emailDefaults?.smtp_password ?? "");
    const [smtpFromEmail, setSmtpFromEmail] = useState(() => emailDefaults?.smtp_from_email ?? "");
    const [smtpUseTls, setSmtpUseTls] = useState(() => emailDefaults?.smtp_use_tls ?? true);
    const [authFrontendBaseUrl, setAuthFrontendBaseUrl] = useState(
        () => emailDefaults?.auth_frontend_base_url ?? "",
    );
    const [authBackendBaseUrl, setAuthBackendBaseUrl] = useState(
        () => emailDefaults?.auth_backend_base_url ?? "",
    );
    const [smtpCheckState, setSmtpCheckState] = useState<{
        loading: boolean;
        message: string | null;
        error: string | null;
    }>({loading: false, message: null, error: null});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [formError, setFormError] = useState<string | null>(null);
    const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
    const [pageLocale, setPageLocale] = useState(initialLocale);

    useEffect(() => {
        const nextSupported = normalizedSeedLocales.join(", ");
        setSupportedLocalesRaw(nextSupported);
    }, [normalizedSeedLocales]);

    useEffect(() => {
        const resolved = resolveSetupLocale(defaultLocale);
        if (resolved) {
            setPageLocale(resolved);
        }
    }, [defaultLocale]);

    const copy = useMemo(() => getSetupCopy(pageLocale), [pageLocale]);

    const normalizedLocales = useMemo(
        () => parseLocales(supportedLocalesRaw),
        [supportedLocalesRaw],
    );

    useEffect(() => {
        if (normalizedLocales.length === 0) {
            return;
        }
        if (!normalizedLocales.includes(defaultLocale)) {
            setDefaultLocale(normalizedLocales[0]);
        }
    }, [defaultLocale, normalizedLocales]);

    function validate(): FieldErrors {
        const errors: FieldErrors = {};

        if (!setupToken.trim()) errors.setup_token = copy.validation.setupTokenRequired;
        if (!siteName.trim()) errors.site_name = copy.validation.siteNameRequired;
        if (normalizedLocales.length === 0) {
            errors.supported_locales = copy.validation.supportedLocalesRequired;
        } else if (!normalizedLocales.includes(normalizeLocale(defaultLocale))) {
            errors.supported_locales = copy.validation.supportedMustIncludeDefault;
        }
        if (!adminEmail.trim()) {
            errors.admin_email = copy.validation.adminEmailRequired;
        } else if (!EMAIL_RE.test(adminEmail.trim())) {
            errors.admin_email = copy.validation.invalidEmail;
        }
        if (!adminPassword) {
            errors.admin_password = copy.validation.adminPasswordRequired;
        } else if (adminPassword.length < 8) {
            errors.admin_password = copy.validation.passwordMinLength;
        }

        const hasCoreSmtpValue =
            smtpHost.trim() ||
            smtpPort.trim() ||
            smtpFromEmail.trim();
        if (hasCoreSmtpValue) {
            if (!smtpHost.trim()) errors.smtp_host = copy.validation.smtpHostRequired;
            if (!smtpPort.trim() || Number.isNaN(Number.parseInt(smtpPort, 10))) {
                errors.smtp_port = copy.validation.smtpPortInvalid;
            }
            if (!smtpFromEmail.trim() || !EMAIL_RE.test(smtpFromEmail.trim())) {
                errors.smtp_from_email = copy.validation.smtpFromEmailInvalid;
            }
        }

        return errors;
    }

    async function onCheckEmailSettings() {
        setSmtpCheckState({loading: true, message: null, error: null});
        try {
            const response = await checkSetupEmailSettings({
                smtp_host: smtpHost.trim(),
                smtp_port: Number.parseInt(smtpPort, 10),
                smtp_username: smtpUsername.trim() || undefined,
                smtp_password: smtpPassword || undefined,
                smtp_from_email: smtpFromEmail.trim(),
                smtp_use_tls: smtpUseTls,
            });
            setSmtpCheckState({loading: false, message: response.message, error: null});
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            setSmtpCheckState({
                loading: false,
                message: null,
                error: typeof detail === "string" ? detail : copy.emailSettingsCheckFailed,
            });
        }
    }

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setFormError(null);

        const errors = validate();
        setFieldErrors(errors);
        if (Object.keys(errors).length > 0) return;

        setIsSubmitting(true);
        try {
            await runSetup({
                setup_token: setupToken.trim(),
                site_name: siteName.trim(),
                default_locale: normalizeLocale(defaultLocale),
                supported_locales: normalizedLocales,
                admin_email: adminEmail.trim(),
                admin_password: adminPassword,
                ...(smtpHost.trim() && smtpPort.trim() && smtpFromEmail.trim()
                    ? {
                        smtp_host: smtpHost.trim(),
                        smtp_port: Number.parseInt(smtpPort, 10),
                        smtp_username: smtpUsername.trim() || undefined,
                        smtp_password: smtpPassword || undefined,
                        smtp_from_email: smtpFromEmail.trim(),
                        smtp_use_tls: smtpUseTls,
                    }
                    : {}),
                ...(authFrontendBaseUrl.trim()
                    ? { auth_frontend_base_url: authFrontendBaseUrl.trim() }
                    : {}),
                ...(authBackendBaseUrl.trim()
                    ? { auth_backend_base_url: authBackendBaseUrl.trim() }
                    : {}),
            });
            onSetupComplete();
            navigate("/login", {replace: true});
        } catch (err: any) {
            const apiDetail = err?.response?.data?.detail;
            setFormError(typeof apiDetail === "string" ? apiDetail : copy.genericError);
        } finally {
            setIsSubmitting(false);
        }
    }

    if (isInitialized) {
        return (
            <div className="ace-page-shell flex items-center justify-center">
                <div className="ace-card ace-card-strong ace-card-pad w-full max-w-xl">
                    <h1 className="text-2xl font-semibold text-gray-900">{copy.alreadyConfiguredTitle}</h1>
                    <p className="mt-3 text-gray-700">{copy.alreadyConfiguredDescription}</p>
                    <Link
                        className="inline-block mt-6 text-blue-700 hover:text-blue-900 underline"
                        to="/login"
                    >
                        {copy.goToLogin}
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <form
                onSubmit={onSubmit}
                className="ace-card ace-card-strong ace-card-pad w-full max-w-3xl"
            >
                <h1 className="text-2xl font-semibold text-gray-900">{copy.title}</h1>
                <p className="mt-2 mb-6 text-sm text-gray-600">{copy.subtitle}</p>

                {formError && (
                    <div role="alert" className="mb-4 rounded-md border border-red-300 bg-red-50 p-3 text-red-800">
                        {formError}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="block">
                        <span className="ace-field-label">{copy.initialSetupToken}</span>
                        <input
                            type="password"
                            value={setupToken}
                            onChange={(e) => setSetupToken(e.target.value)}
                            className="ace-input"
                        />
                        {fieldErrors.setup_token && <p className="text-xs text-red-700 mt-1">{fieldErrors.setup_token}</p>}
                    </label>

                    <label className="block">
                        <span className="ace-field-label">{copy.siteName}</span>
                        <input
                            type="text"
                            value={siteName}
                            onChange={(e) => setSiteName(e.target.value)}
                            className="ace-input"
                        />
                        {fieldErrors.site_name && <p className="text-xs text-red-700 mt-1">{fieldErrors.site_name}</p>}
                    </label>

                    <label className="block md:col-span-2">
                        <span className="ace-field-label">{copy.supportedLocales}</span>
                        <input
                            type="text"
                            value={supportedLocalesRaw}
                            readOnly
                            className="ace-input"
                        />
                        <p className="text-xs text-gray-500 mt-1">{copy.localesHint}</p>
                        {fieldErrors.supported_locales && <p className="text-xs text-red-700 mt-1">{fieldErrors.supported_locales}</p>}
                    </label>

                    <label className="block">
                        <span className="ace-field-label">{copy.adminEmail}</span>
                        <input
                            type="email"
                            value={adminEmail}
                            onChange={(e) => setAdminEmail(e.target.value)}
                            className="ace-input"
                        />
                        {fieldErrors.admin_email && <p className="text-xs text-red-700 mt-1">{fieldErrors.admin_email}</p>}
                    </label>

                    <label className="block">
                        <span className="ace-field-label">{copy.adminPassword}</span>
                        <input
                            type="password"
                            value={adminPassword}
                            onChange={(e) => setAdminPassword(e.target.value)}
                            className="ace-input"
                        />
                        {fieldErrors.admin_password && <p className="text-xs text-red-700 mt-1">{fieldErrors.admin_password}</p>}
                    </label>
                </div>

                <div className="mt-6 rounded-lg border border-gray-200 p-4">
                    <h2 className="text-lg font-semibold text-gray-900">{copy.optionalEmailSettings}</h2>
                    <p className="mt-1 text-sm text-gray-600">
                        {copy.optionalEmailSettingsHint}
                    </p>
                    <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <label className="block">
                            <span className="ace-field-label">{copy.smtpHost}</span>
                            <input type="text" value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)} className="ace-input" />
                            {fieldErrors.smtp_host && <p className="text-xs text-red-700 mt-1">{fieldErrors.smtp_host}</p>}
                        </label>
                        <label className="block">
                            <span className="ace-field-label">{copy.smtpPort}</span>
                            <input type="number" value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)} className="ace-input" />
                            {fieldErrors.smtp_port && <p className="text-xs text-red-700 mt-1">{fieldErrors.smtp_port}</p>}
                        </label>
                        <label className="block">
                            <span className="ace-field-label">{copy.smtpUsername}</span>
                            <input type="text" value={smtpUsername} onChange={(e) => setSmtpUsername(e.target.value)} className="ace-input" />
                        </label>
                        <label className="block">
                            <span className="ace-field-label">{copy.smtpPassword}</span>
                            <input type="password" value={smtpPassword} onChange={(e) => setSmtpPassword(e.target.value)} className="ace-input" />
                        </label>
                        <label className="block md:col-span-2">
                            <span className="ace-field-label">{copy.smtpFromEmail}</span>
                            <input type="email" value={smtpFromEmail} onChange={(e) => setSmtpFromEmail(e.target.value)} className="ace-input" />
                            {fieldErrors.smtp_from_email && <p className="text-xs text-red-700 mt-1">{fieldErrors.smtp_from_email}</p>}
                        </label>
                        <label className="flex items-center gap-2 md:col-span-2">
                            <input type="checkbox" checked={smtpUseTls} onChange={(e) => setSmtpUseTls(e.target.checked)} />
                            <span className="text-sm text-gray-700">{copy.smtpUseStartTls}</span>
                        </label>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-3">
                        <button type="button" onClick={onCheckEmailSettings} className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50" disabled={smtpCheckState.loading}>
                            {smtpCheckState.loading ? copy.checkingEmailSettings : copy.checkEmailSettings}
                        </button>
                        {smtpCheckState.message && <p className="text-sm text-green-700">{smtpCheckState.message}</p>}
                        {smtpCheckState.error && <p className="text-sm text-red-700">{smtpCheckState.error}</p>}
                    </div>
                </div>

                <div className="mt-6 rounded-lg border border-gray-200 p-4">
                    <h2 className="text-lg font-semibold text-gray-900">{copy.authBaseUrls}</h2>
                    <p className="mt-1 text-sm text-gray-600">{copy.authBaseUrlsHint}</p>
                    <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <label className="block">
                            <span className="ace-field-label">{copy.authFrontendBaseUrl}</span>
                            <input type="url" value={authFrontendBaseUrl} onChange={(e) => setAuthFrontendBaseUrl(e.target.value)} className="ace-input" />
                        </label>
                        <label className="block">
                            <span className="ace-field-label">{copy.authBackendBaseUrl}</span>
                            <input type="url" value={authBackendBaseUrl} onChange={(e) => setAuthBackendBaseUrl(e.target.value)} className="ace-input" />
                        </label>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="ace-primary-btn mt-6 py-2.5"
                >
                    {isSubmitting ? copy.initializing : copy.initialize}
                </button>
            </form>
        </div>
    );
}

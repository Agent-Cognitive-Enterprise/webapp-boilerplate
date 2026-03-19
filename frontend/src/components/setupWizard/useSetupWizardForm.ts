import {useEffect, useMemo, useState} from "react";
import {checkSetupEmailSettings, runSetup} from "../../api/setup";
import {
    getSetupCopy,
    normalizeLocale,
    resolveSetupLocale,
} from "../../i18n/setupWizardLocales";
import type {FieldErrors, SetupEmailDefaults} from "./types";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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

export function resolveBrowserLocale(availableLocales: string[]): string {
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

type UseSetupWizardFormArgs = {
    seedLocales: string[];
    emailDefaults: SetupEmailDefaults;
    onSetupComplete: () => void;
};

export function useSetupWizardForm({
    seedLocales,
    emailDefaults,
    onSetupComplete,
}: UseSetupWizardFormArgs) {
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
    const [authFrontendBaseUrl, setAuthFrontendBaseUrl] = useState(() => emailDefaults?.auth_frontend_base_url ?? "");
    const [authBackendBaseUrl, setAuthBackendBaseUrl] = useState(() => emailDefaults?.auth_backend_base_url ?? "");
    const [smtpCheckState, setSmtpCheckState] = useState({
        loading: false,
        message: null as string | null,
        error: null as string | null,
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [formError, setFormError] = useState<string | null>(null);
    const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
    const [pageLocale, setPageLocale] = useState(initialLocale);

    useEffect(() => {
        setSupportedLocalesRaw(normalizedSeedLocales.join(", "));
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

    const validate = (): FieldErrors => {
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

        const hasCoreSmtpValue = smtpHost.trim() || smtpPort.trim() || smtpFromEmail.trim();

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
    };

    const onCheckEmailSettings = async () => {
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
    };

    const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setFormError(null);

        const errors = validate();
        setFieldErrors(errors);

        if (Object.keys(errors).length > 0) {
            return;
        }

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
                    ? {auth_frontend_base_url: authFrontendBaseUrl.trim()}
                    : {}),
                ...(authBackendBaseUrl.trim()
                    ? {auth_backend_base_url: authBackendBaseUrl.trim()}
                    : {}),
            });

            onSetupComplete();

            // If router-driven navigation loses a race after setup, force the browser off /setup.
            window.setTimeout(() => {
                if (window.location.pathname === "/setup") {
                    window.location.replace("/login");
                }
            }, 0);
        } catch (err: any) {
            const apiDetail = err?.response?.data?.detail;
            setFormError(typeof apiDetail === "string" ? apiDetail : copy.genericError);
        } finally {
            setIsSubmitting(false);
        }
    };

    return {
        copy,
        setupToken,
        setSetupToken,
        siteName,
        setSiteName,
        supportedLocalesRaw,
        adminEmail,
        setAdminEmail,
        adminPassword,
        setAdminPassword,
        smtpHost,
        setSmtpHost,
        smtpPort,
        setSmtpPort,
        smtpUsername,
        setSmtpUsername,
        smtpPassword,
        setSmtpPassword,
        smtpFromEmail,
        setSmtpFromEmail,
        smtpUseTls,
        setSmtpUseTls,
        authFrontendBaseUrl,
        setAuthFrontendBaseUrl,
        authBackendBaseUrl,
        setAuthBackendBaseUrl,
        smtpCheckState,
        isSubmitting,
        formError,
        fieldErrors,
        onCheckEmailSettings,
        onSubmit,
    };
}

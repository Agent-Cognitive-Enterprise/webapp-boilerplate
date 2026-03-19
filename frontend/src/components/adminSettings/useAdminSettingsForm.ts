import {useContext, useEffect, useMemo, useState} from "react";
import type {ChangeEvent, FormEvent} from "react";

import {AuthContext} from "../../contexts/AuthContext.tsx";
import {
    checkAdminEmailSettings,
    getAdminSettings,
    type AdminSettingsUpdatePayload,
    updateAdminSettings,
} from "../../api/adminSettings.ts";
import {
    EXISTING_SECRET_PLACEHOLDER,
    fileToDataUrl,
    parseSupportedLocales,
    resolveAdminSettingsLocale,
} from "./adminSettingsUtils.ts";

type AdminSettingsFormText = {
    emailSettingsCheckFailedText: string;
    loadFailedText: string;
    saveFailedText: string;
    updatedText: string;
};

export function useAdminSettingsForm(text: AdminSettingsFormText) {
    const auth = useContext(AuthContext);
    const isAuthResolving = Boolean(auth?.token && !auth.user);
    const isAdmin = Boolean(auth?.user?.is_admin);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [siteName, setSiteName] = useState("");
    const [supportedLocalesRaw, setSupportedLocalesRaw] = useState("en");
    const [adminEmail, setAdminEmail] = useState("");
    const [adminPassword, setAdminPassword] = useState(EXISTING_SECRET_PLACEHOLDER);
    const [openAiKey, setOpenAiKey] = useState("");
    const [deepSeekKey, setDeepSeekKey] = useState("");
    const [adminPasswordDirty, setAdminPasswordDirty] = useState(false);
    const [openAiKeyDirty, setOpenAiKeyDirty] = useState(false);
    const [deepSeekKeyDirty, setDeepSeekKeyDirty] = useState(false);
    const [openAiMasked, setOpenAiMasked] = useState<string | null>(null);
    const [deepSeekMasked, setDeepSeekMasked] = useState<string | null>(null);
    const [siteLogo, setSiteLogo] = useState<string | null>(null);
    const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
    const [smtpHost, setSmtpHost] = useState("");
    const [smtpPort, setSmtpPort] = useState("");
    const [smtpUsername, setSmtpUsername] = useState("");
    const [smtpPassword, setSmtpPassword] = useState("");
    const [smtpPasswordDirty, setSmtpPasswordDirty] = useState(false);
    const [smtpFromEmail, setSmtpFromEmail] = useState("");
    const [smtpUseTls, setSmtpUseTls] = useState(true);
    const [authFrontendBaseUrl, setAuthFrontendBaseUrl] = useState("");
    const [authBackendBaseUrl, setAuthBackendBaseUrl] = useState("");
    const [emailConfigured, setEmailConfigured] = useState(false);
    const [smtpCheckLoading, setSmtpCheckLoading] = useState(false);
    const [smtpCheckMessage, setSmtpCheckMessage] = useState<string | null>(null);
    const [smtpCheckError, setSmtpCheckError] = useState<string | null>(null);

    const pageLocale = useMemo(resolveAdminSettingsLocale, []);
    const supportedLocales = useMemo(() => parseSupportedLocales(supportedLocalesRaw), [supportedLocalesRaw]);
    const hasAiKeyConfigured = Boolean(
        (openAiMasked && openAiMasked.length > 0) ||
        (deepSeekMasked && deepSeekMasked.length > 0) ||
        openAiKey.trim() ||
        deepSeekKey.trim(),
    );

    useEffect(() => {
        if (isAuthResolving) {
            return;
        }

        if (!isAdmin) {
            setLoading(false);
            return;
        }

        let active = true;
        setLoading(true);
        const load = async () => {
            try {
                const data = await getAdminSettings();
                if (!active) return;
                setSiteName(data.site_name ?? "");
                setSupportedLocalesRaw((data.supported_locales ?? ["en"]).join(", "));
                setAdminEmail(data.admin_email);
                setOpenAiMasked(data.openai_api_key_masked);
                setDeepSeekMasked(data.deepseek_api_key_masked);
                setOpenAiKey(data.openai_api_key_masked ?? "");
                setDeepSeekKey(data.deepseek_api_key_masked ?? "");
                setOpenAiKeyDirty(false);
                setDeepSeekKeyDirty(false);
                setAdminPassword(EXISTING_SECRET_PLACEHOLDER);
                setAdminPasswordDirty(false);
                setSiteLogo(data.site_logo);
                setBackgroundImage(data.background_image);
                setSmtpHost(data.smtp_host ?? "");
                setSmtpPort(data.smtp_port ? String(data.smtp_port) : "");
                setSmtpUsername(data.smtp_username ?? "");
                setSmtpPassword(data.smtp_password_masked ? EXISTING_SECRET_PLACEHOLDER : "");
                setSmtpPasswordDirty(false);
                setSmtpFromEmail(data.smtp_from_email ?? "");
                setSmtpUseTls(data.smtp_use_tls);
                setAuthFrontendBaseUrl(data.auth_frontend_base_url ?? "");
                setAuthBackendBaseUrl(data.auth_backend_base_url ?? "");
                setEmailConfigured(data.email_configured);
            } catch (err: any) {
                if (!active) return;
                setError(err?.response?.data?.detail ?? text.loadFailedText);
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        };
        void load();
        return () => {
            active = false;
        };
    }, [isAdmin, isAuthResolving, text.loadFailedText]);

    async function handleLogoChange(event: ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        if (!file) return;
        setSiteLogo(await fileToDataUrl(file));
    }

    async function handleBackgroundChange(event: ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        if (!file) return;
        setBackgroundImage(await fileToDataUrl(file));
    }

    async function onSave(event: FormEvent) {
        event.preventDefault();
        setError(null);
        setSuccess(null);

        const payload: AdminSettingsUpdatePayload = {
            site_name: siteName.trim(),
            supported_locales: supportedLocales,
            admin_email: adminEmail.trim(),
            site_logo: siteLogo,
            background_image: backgroundImage,
            smtp_host: smtpHost.trim() || null,
            smtp_port: smtpPort.trim() ? Number.parseInt(smtpPort, 10) : null,
            smtp_username: smtpUsername.trim() || null,
            smtp_from_email: smtpFromEmail.trim() || null,
            smtp_use_tls: smtpUseTls,
            auth_frontend_base_url: authFrontendBaseUrl.trim() || null,
            auth_backend_base_url: authBackendBaseUrl.trim() || null,
        };

        if (adminPasswordDirty && adminPassword.trim()) payload.admin_password = adminPassword;
        if (openAiKeyDirty && openAiKey.trim()) payload.openai_api_key = openAiKey.trim();
        if (deepSeekKeyDirty && deepSeekKey.trim()) payload.deepseek_api_key = deepSeekKey.trim();
        if (smtpPasswordDirty && smtpPassword) payload.smtp_password = smtpPassword;

        setSaving(true);
        try {
            const updated = await updateAdminSettings(payload);
            setOpenAiKey(updated.openai_api_key_masked ?? "");
            setDeepSeekKey(updated.deepseek_api_key_masked ?? "");
            setAdminPassword(EXISTING_SECRET_PLACEHOLDER);
            setOpenAiKeyDirty(false);
            setDeepSeekKeyDirty(false);
            setAdminPasswordDirty(false);
            setOpenAiMasked(updated.openai_api_key_masked);
            setDeepSeekMasked(updated.deepseek_api_key_masked);
            setSmtpPassword(updated.smtp_password_masked ? EXISTING_SECRET_PLACEHOLDER : "");
            setSmtpPasswordDirty(false);
            setEmailConfigured(updated.email_configured);
            setAuthFrontendBaseUrl(updated.auth_frontend_base_url ?? "");
            setAuthBackendBaseUrl(updated.auth_backend_base_url ?? "");
            setSuccess(text.updatedText);
            window.location.reload();
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            if (typeof detail === "string") setError(detail);
            else if (detail?.message) setError(detail.message);
            else setError(text.saveFailedText);
        } finally {
            setSaving(false);
        }
    }

    async function onCheckEmailSettings() {
        setSmtpCheckLoading(true);
        setSmtpCheckError(null);
        setSmtpCheckMessage(null);
        try {
            const result = await checkAdminEmailSettings({
                smtp_host: smtpHost.trim() || undefined,
                smtp_port: smtpPort.trim() ? Number.parseInt(smtpPort, 10) : undefined,
                smtp_username: smtpUsername.trim() || undefined,
                smtp_password: smtpPasswordDirty && smtpPassword ? smtpPassword : undefined,
                smtp_from_email: smtpFromEmail.trim() || undefined,
                smtp_use_tls: smtpUseTls,
            });
            setSmtpCheckMessage(result.message);
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            setSmtpCheckError(typeof detail === "string" ? detail : text.emailSettingsCheckFailedText);
        } finally {
            setSmtpCheckLoading(false);
        }
    }

    return {
        pageLocale,
        isAdmin,
        isAuthResolving,
        loading,
        saving,
        error,
        success,
        siteName,
        supportedLocalesRaw,
        adminEmail,
        adminPassword,
        openAiKey,
        deepSeekKey,
        adminPasswordDirty,
        openAiMasked,
        deepSeekMasked,
        siteLogo,
        backgroundImage,
        smtpHost,
        smtpPort,
        smtpUsername,
        smtpPassword,
        smtpPasswordDirty,
        smtpFromEmail,
        smtpUseTls,
        authFrontendBaseUrl,
        authBackendBaseUrl,
        emailConfigured,
        smtpCheckLoading,
        smtpCheckMessage,
        smtpCheckError,
        hasAiKeyConfigured,
        setSiteName,
        setSupportedLocalesRaw,
        setAdminEmail,
        setAdminPassword,
        setOpenAiKey,
        setDeepSeekKey,
        setAdminPasswordDirty,
        setOpenAiKeyDirty,
        setDeepSeekKeyDirty,
        setSmtpHost,
        setSmtpPort,
        setSmtpUsername,
        setSmtpPassword,
        setSmtpPasswordDirty,
        setSmtpFromEmail,
        setSmtpUseTls,
        setAuthFrontendBaseUrl,
        setAuthBackendBaseUrl,
        handleLogoChange,
        handleBackgroundChange,
        onSave,
        onCheckEmailSettings,
    };
}

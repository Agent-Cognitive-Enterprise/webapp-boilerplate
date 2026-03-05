import {useContext, useEffect, useMemo, useState} from "react";
import type {ChangeEvent, FormEvent} from "react";
import {Navigate} from "react-router-dom";

import {AuthContext} from "../contexts/AuthContext.tsx";
import {
    checkAdminEmailSettings,
    getAdminSettings,
    type AdminSettingsUpdatePayload,
    updateAdminSettings,
} from "../api/adminSettings.ts";
import {normalizeLocale} from "../i18n/setupWizardLocales.ts";
import {useT} from "../hooks/useT.ts";

const EXISTING_SECRET_PLACEHOLDER = "********";

async function fileToDataUrl(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(new Error("Failed to read file"));
        reader.readAsDataURL(file);
    });
}

function parseSupportedLocales(raw: string): string[] {
    const normalized: string[] = [];
    for (const locale of raw.split(",")) {
        const value = normalizeLocale(locale);
        if (!value) continue;
        if (!normalized.includes(value)) normalized.push(value);
    }
    return normalized;
}

export default function AdminSettings() {
    const auth = useContext(AuthContext);
    const isAuthResolving = Boolean(auth?.token && !auth.user);
    const isAdmin = Boolean(auth?.user?.is_admin);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const pageLocale = useMemo(
        () => normalizeLocale(localStorage.getItem("uiLocale") || navigator.language?.slice(0, 2) || "en") || "en",
        [],
    );

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

    const supportedLocales = useMemo(() => parseSupportedLocales(supportedLocalesRaw), [supportedLocalesRaw]);
    const titleText = useT("dashboard.link.admin_settings", undefined, "Admin settings", pageLocale);
    const aiKeysText = useT("admin.settings.ai_keys", undefined, "AI API keys", pageLocale);
    const openAiKeyText = useT("admin.settings.openai_api_key", undefined, "OpenAI API key", pageLocale);
    const deepSeekKeyText = useT("admin.settings.deepseek_api_key", undefined, "DeepSeek API key", pageLocale);
    const siteLogoText = useT("admin.settings.site_logo", undefined, "Site logo", pageLocale);
    const backgroundImageText = useT("admin.settings.background_image", undefined, "Background image", pageLocale);
    const saveText = useT("admin.settings.save", undefined, "Save settings", pageLocale);
    const savingText = useT("admin.settings.saving", undefined, "Saving...", pageLocale);
    const updatedText = useT("admin.settings.updated", undefined, "Settings updated.", pageLocale);
    const loadingText = useT("admin.settings.loading", undefined, "Loading admin settings...", pageLocale);
    const siteLogoPreviewAltText = useT(
        "admin.settings.site_logo_preview",
        undefined,
        "Site logo preview",
        pageLocale,
    );
    const backgroundPreviewAltText = useT(
        "admin.settings.background_image_preview",
        undefined,
        "Background image preview",
        pageLocale,
    );
    const translationWarningMissingKeysText = useT(
        "admin.settings.translation_warning_missing_keys",
        undefined,
        "Automatic translations require at least one provider key (OpenAI or DeepSeek).",
        pageLocale,
    );
    const translationWarningAutoText = useT(
        "admin.settings.translation_warning_auto",
        undefined,
        "When API keys are provided, new locales are translated automatically on first encounter. If OpenAI is unavailable, DeepSeek is used when configured.",
        pageLocale,
    );
    const emailSettingsTitleText = useT("admin.email.settings.title", undefined, "Email settings", pageLocale);
    const emailEnabledStatusText = useT(
        "admin.email.settings.status.enabled",
        undefined,
        "Email verification is enabled for self-registered users.",
        pageLocale,
    );
    const emailDisabledStatusText = useT(
        "admin.email.settings.status.disabled",
        undefined,
        "Email is not configured. Self-registered users can log in without verification.",
        pageLocale,
    );
    const smtpHostText = useT("admin.email.settings.smtp_host", undefined, "SMTP host", pageLocale);
    const smtpPortText = useT("admin.email.settings.smtp_port", undefined, "SMTP port", pageLocale);
    const smtpUsernameText = useT("admin.email.settings.smtp_username", undefined, "SMTP username", pageLocale);
    const smtpPasswordText = useT("admin.email.settings.smtp_password", undefined, "SMTP password", pageLocale);
    const smtpFromEmailText = useT("admin.email.settings.smtp_from_email", undefined, "SMTP from email", pageLocale);
    const smtpUseStartTlsText = useT("admin.email.settings.smtp_use_starttls", undefined, "Use STARTTLS", pageLocale);
    const authFrontendBaseUrlText = useT(
        "admin.auth.base_url.frontend",
        undefined,
        "Frontend base URL",
        pageLocale,
    );
    const authBackendBaseUrlText = useT(
        "admin.auth.base_url.backend",
        undefined,
        "Backend base URL",
        pageLocale,
    );
    const authBaseUrlsTitleText = useT(
        "setup.auth.base_urls",
        undefined,
        "Authentication base URLs",
        pageLocale,
    );
    const authBaseUrlsHintText = useT(
        "setup.auth.base_urls_hint",
        undefined,
        "Used in verification and reset links sent by email.",
        pageLocale,
    );
    const checkEmailSettingsText = useT("admin.email.settings.check", undefined, "Check email settings", pageLocale);
    const checkingEmailSettingsText = useT("admin.email.settings.checking", undefined, "Checking...", pageLocale);
    const emailSettingsCheckFailedText = useT(
        "admin.email.settings.check_failed",
        undefined,
        "Email settings check failed",
        pageLocale,
    );
    const loadFailedText = useT("admin.settings.load_failed", undefined, "Failed to load admin settings", pageLocale);
    const saveFailedText = useT("admin.settings.save_failed", undefined, "Failed to save admin settings", pageLocale);
    const siteNameText = useT("setup.field.site_name", undefined, "Site name", pageLocale);
    const supportedLocalesText = useT("setup.field.supported_locales", undefined, "Supported locales", pageLocale);
    const supportedLocalesHintText = useT("setup.hint.supported_locales", undefined, "Comma-separated locale codes.", pageLocale);
    const adminEmailText = useT("setup.field.admin_email", undefined, "Admin email", pageLocale);
    const adminPasswordText = useT("setup.field.admin_password", undefined, "Admin password", pageLocale);

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
                setError(err?.response?.data?.detail ?? loadFailedText);
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
    }, [isAdmin, isAuthResolving, loadFailedText]);

    async function handleLogoChange(e: ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (!file) return;
        setSiteLogo(await fileToDataUrl(file));
    }

    async function handleBackgroundChange(e: ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
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
            setSuccess(updatedText);
            window.location.reload();
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            if (typeof detail === "string") setError(detail);
            else if (detail?.message) setError(detail.message);
            else setError(saveFailedText);
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
            setSmtpCheckError(typeof detail === "string" ? detail : emailSettingsCheckFailedText);
        } finally {
            setSmtpCheckLoading(false);
        }
    }

    const hasAiKeyConfigured = Boolean(
        (openAiMasked && openAiMasked.length > 0) ||
        (deepSeekMasked && deepSeekMasked.length > 0) ||
        openAiKey.trim() ||
        deepSeekKey.trim(),
    );

    if (isAuthResolving || loading) {
        return <div className="ace-page-shell text-center text-white">{loadingText}</div>;
    }

    if (!isAdmin) {
        return <Navigate to="/dashboard" replace/>;
    }

    return (
        <div className="ace-page-shell" key={pageLocale}>
            <div className="ace-card ace-card-strong ace-card-pad mx-auto max-w-4xl">
                <h1 className="mb-4 text-2xl font-bold text-gray-900 sm:text-3xl">{titleText}</h1>
                {error && <div className="mb-4 rounded border border-red-300 bg-red-50 px-3 py-2 text-red-700">{error}</div>}
                {success && <div className="mb-4 rounded border border-green-300 bg-green-50 px-3 py-2 text-green-700">{success}</div>}

                <form onSubmit={onSave} className="space-y-6">
                    <div className="grid grid-cols-1 gap-4">
                        <label className="block">
                            <span className="text-sm font-medium text-gray-700">{siteNameText}</span>
                            <input
                                aria-label={siteNameText}
                                className="ace-input"
                                value={siteName}
                                onChange={(e) => setSiteName(e.target.value)}
                            />
                        </label>

                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <label className="block">
                                <span className="text-sm font-medium text-gray-700">{siteLogoText}</span>
                                <input aria-label={siteLogoText} type="file" accept="image/*" className="ace-input" onChange={handleLogoChange}/>
                                {siteLogo && (
                                    <img src={siteLogo} alt={siteLogoPreviewAltText} className="mt-2 max-h-24 object-contain border rounded p-2"/>
                                )}
                            </label>
                            <label className="block">
                                <span className="text-sm font-medium text-gray-700">{backgroundImageText}</span>
                                <input aria-label={backgroundImageText} type="file" accept="image/*" className="ace-input" onChange={handleBackgroundChange}/>
                                {backgroundImage && (
                                    <img src={backgroundImage} alt={backgroundPreviewAltText} className="mt-2 max-h-24 object-cover border rounded"/>
                                )}
                            </label>
                        </div>

                        <div className="grid grid-cols-1 gap-4">
                            <label className="block w-full">
                                <span className="text-sm font-medium text-gray-700">{supportedLocalesText}</span>
                                <input
                                    aria-label={supportedLocalesText}
                                    className="ace-input"
                                    value={supportedLocalesRaw}
                                    onChange={(e) => setSupportedLocalesRaw(e.target.value)}
                                />
                                <p className="text-xs text-gray-500 mt-1">{supportedLocalesHintText}</p>
                            </label>
                        </div>

                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <label className="block">
                                <span className="text-sm font-medium text-gray-700">{adminEmailText}</span>
                                <input aria-label={adminEmailText} type="email" className="ace-input" value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)}/>
                            </label>
                            <label className="block">
                                <span className="text-sm font-medium text-gray-700">{adminPasswordText}</span>
                                <input
                                    aria-label={adminPasswordText}
                                    type="password"
                                    autoComplete="off"
                                    className="ace-input"
                                    value={adminPassword}
                                    onFocus={() => {
                                        if (!adminPasswordDirty) {
                                            setAdminPassword("");
                                        }
                                    }}
                                    onChange={(e) => {
                                        setAdminPasswordDirty(true);
                                        setAdminPassword(e.target.value);
                                    }}
                                />
                            </label>
                        </div>

                        <div className="rounded border border-slate-200 bg-slate-50 p-4">
                            <h2 className="text-sm font-semibold text-gray-800 mb-3">{aiKeysText}</h2>
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                <label className="block">
                                    <span className="text-sm font-medium text-gray-700">{openAiKeyText}</span>
                                    <input
                                        aria-label={openAiKeyText}
                                        type="password"
                                        autoComplete="off"
                                        className="ace-input"
                                        value={openAiKey}
                                        onChange={(e) => {
                                            setOpenAiKeyDirty(true);
                                            setOpenAiKey(e.target.value);
                                        }}
                                    />
                                </label>
                                <label className="block">
                                    <span className="text-sm font-medium text-gray-700">{deepSeekKeyText}</span>
                                    <input
                                        aria-label={deepSeekKeyText}
                                        type="password"
                                        autoComplete="off"
                                        className="ace-input"
                                        value={deepSeekKey}
                                        onChange={(e) => {
                                            setDeepSeekKeyDirty(true);
                                            setDeepSeekKey(e.target.value);
                                        }}
                                    />
                                </label>
                            </div>
                            <div className={`mt-3 rounded border px-3 py-2 text-xs ${hasAiKeyConfigured ? "border-blue-200 bg-blue-50 text-blue-800" : "border-amber-200 bg-amber-50 text-amber-800"}`}>
                                {!hasAiKeyConfigured && <p>{translationWarningMissingKeysText}</p>}
                                <p>{translationWarningAutoText}</p>
                            </div>
                        </div>

                        <div className="rounded border border-slate-200 bg-slate-50 p-4">
                            <h2 className="text-sm font-semibold text-gray-800 mb-3">{emailSettingsTitleText}</h2>
                            <p className={`mb-3 text-xs ${emailConfigured ? "text-green-700" : "text-gray-600"}`}>
                                {emailConfigured
                                    ? emailEnabledStatusText
                                    : emailDisabledStatusText}
                            </p>
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                <label className="block">
                                    <span className="text-sm font-medium text-gray-700">{smtpHostText}</span>
                                    <input className="ace-input" value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)} />
                                </label>
                                <label className="block">
                                    <span className="text-sm font-medium text-gray-700">{smtpPortText}</span>
                                    <input type="number" className="ace-input" value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)} />
                                </label>
                                <label className="block">
                                    <span className="text-sm font-medium text-gray-700">{smtpUsernameText}</span>
                                    <input className="ace-input" value={smtpUsername} onChange={(e) => setSmtpUsername(e.target.value)} />
                                </label>
                                <label className="block">
                                    <span className="text-sm font-medium text-gray-700">{smtpPasswordText}</span>
                                    <input
                                        type="password"
                                        className="ace-input"
                                        value={smtpPassword}
                                        onFocus={() => {
                                            if (!smtpPasswordDirty && smtpPassword === EXISTING_SECRET_PLACEHOLDER) {
                                                setSmtpPassword("");
                                            }
                                        }}
                                        onChange={(e) => {
                                            setSmtpPasswordDirty(true);
                                            setSmtpPassword(e.target.value);
                                        }}
                                    />
                                </label>
                                <label className="block md:col-span-2">
                                    <span className="text-sm font-medium text-gray-700">{smtpFromEmailText}</span>
                                    <input type="email" className="ace-input" value={smtpFromEmail} onChange={(e) => setSmtpFromEmail(e.target.value)} />
                                </label>
                                <label className="flex items-center gap-2 md:col-span-2">
                                    <input type="checkbox" checked={smtpUseTls} onChange={(e) => setSmtpUseTls(e.target.checked)} />
                                    <span className="text-sm text-gray-700">{smtpUseStartTlsText}</span>
                                </label>
                            </div>
                            <div className="mt-3 flex flex-wrap items-center gap-3">
                                <button type="button" className="rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100" onClick={onCheckEmailSettings} disabled={smtpCheckLoading}>
                                    {smtpCheckLoading ? checkingEmailSettingsText : checkEmailSettingsText}
                                </button>
                                {smtpCheckMessage && <p className="text-sm text-green-700">{smtpCheckMessage}</p>}
                                {smtpCheckError && <p className="text-sm text-red-700">{smtpCheckError}</p>}
                            </div>
                        </div>

                        <div className="rounded border border-slate-200 bg-slate-50 p-4">
                            <h2 className="text-sm font-semibold text-gray-800 mb-1">{authBaseUrlsTitleText}</h2>
                            <p className="mb-3 text-xs text-gray-600">{authBaseUrlsHintText}</p>
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                <label className="block">
                                    <span className="text-sm font-medium text-gray-700">{authFrontendBaseUrlText}</span>
                                    <input type="url" className="ace-input" value={authFrontendBaseUrl} onChange={(e) => setAuthFrontendBaseUrl(e.target.value)} />
                                </label>
                                <label className="block">
                                    <span className="text-sm font-medium text-gray-700">{authBackendBaseUrlText}</span>
                                    <input type="url" className="ace-input" value={authBackendBaseUrl} onChange={(e) => setAuthBackendBaseUrl(e.target.value)} />
                                </label>
                            </div>
                        </div>
                    </div>

                    <button type="submit" disabled={saving} className="rounded bg-blue-700 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:bg-gray-400">
                        {saving ? savingText : saveText}
                    </button>
                </form>
            </div>
        </div>
    );
}

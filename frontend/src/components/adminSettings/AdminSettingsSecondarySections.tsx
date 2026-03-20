import {EXISTING_SECRET_PLACEHOLDER} from "./adminSettingsUtils.ts";

type EmailSettingsSectionProps = {
    emailSettingsTitleText: string;
    emailConfigured: boolean;
    emailEnabledStatusText: string;
    emailDisabledStatusText: string;
    smtpHostText: string;
    smtpHost: string;
    setSmtpHost: (value: string) => void;
    smtpPortText: string;
    smtpPort: string;
    setSmtpPort: (value: string) => void;
    smtpUsernameText: string;
    smtpUsername: string;
    setSmtpUsername: (value: string) => void;
    smtpPasswordText: string;
    smtpPassword: string;
    smtpPasswordDirty: boolean;
    setSmtpPassword: (value: string) => void;
    setSmtpPasswordDirty: (value: boolean) => void;
    smtpFromEmailText: string;
    smtpFromEmail: string;
    setSmtpFromEmail: (value: string) => void;
    smtpUseTls: boolean;
    setSmtpUseTls: (value: boolean) => void;
    smtpUseStartTlsText: string;
    onCheckEmailSettings: () => void | Promise<void>;
    smtpCheckLoading: boolean;
    checkEmailSettingsText: string;
    checkingEmailSettingsText: string;
    smtpCheckMessage: string | null;
    smtpCheckError: string | null;
};

type AuthBaseUrlsSectionProps = {
    authBaseUrlsTitleText: string;
    authBaseUrlsHintText: string;
    authFrontendBaseUrlText: string;
    authFrontendBaseUrl: string;
    setAuthFrontendBaseUrl: (value: string) => void;
    authBackendBaseUrlText: string;
    authBackendBaseUrl: string;
    setAuthBackendBaseUrl: (value: string) => void;
};

export function EmailSettingsSection({
    emailSettingsTitleText,
    emailConfigured,
    emailEnabledStatusText,
    emailDisabledStatusText,
    smtpHostText,
    smtpHost,
    setSmtpHost,
    smtpPortText,
    smtpPort,
    setSmtpPort,
    smtpUsernameText,
    smtpUsername,
    setSmtpUsername,
    smtpPasswordText,
    smtpPassword,
    smtpPasswordDirty,
    setSmtpPassword,
    setSmtpPasswordDirty,
    smtpFromEmailText,
    smtpFromEmail,
    setSmtpFromEmail,
    smtpUseTls,
    setSmtpUseTls,
    smtpUseStartTlsText,
    onCheckEmailSettings,
    smtpCheckLoading,
    checkEmailSettingsText,
    checkingEmailSettingsText,
    smtpCheckMessage,
    smtpCheckError,
}: EmailSettingsSectionProps) {
    return (
        <div className="rounded border border-slate-200 bg-slate-50 p-4">
            <h2 className="mb-3 text-sm font-semibold text-gray-800">{emailSettingsTitleText}</h2>
            <p className={`mb-3 text-xs ${emailConfigured ? "text-green-700" : "text-gray-600"}`}>
                {emailConfigured ? emailEnabledStatusText : emailDisabledStatusText}
            </p>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{smtpHostText}</span>
                    <input
                        aria-label={smtpHostText}
                        className="ace-input"
                        value={smtpHost}
                        onChange={(event) => setSmtpHost(event.target.value)}
                    />
                </label>
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{smtpPortText}</span>
                    <input
                        aria-label={smtpPortText}
                        type="number"
                        className="ace-input"
                        value={smtpPort}
                        onChange={(event) => setSmtpPort(event.target.value)}
                    />
                </label>
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{smtpUsernameText}</span>
                    <input
                        aria-label={smtpUsernameText}
                        className="ace-input"
                        value={smtpUsername}
                        onChange={(event) => setSmtpUsername(event.target.value)}
                    />
                </label>
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{smtpPasswordText}</span>
                    <input
                        aria-label={smtpPasswordText}
                        type="password"
                        className="ace-input"
                        value={smtpPassword}
                        onFocus={() => {
                            if (!smtpPasswordDirty && smtpPassword === EXISTING_SECRET_PLACEHOLDER) {
                                setSmtpPassword("");
                            }
                        }}
                        onChange={(event) => {
                            setSmtpPasswordDirty(true);
                            setSmtpPassword(event.target.value);
                        }}
                    />
                </label>
                <label className="block md:col-span-2">
                    <span className="text-sm font-medium text-gray-700">{smtpFromEmailText}</span>
                    <input
                        aria-label={smtpFromEmailText}
                        type="email"
                        className="ace-input"
                        value={smtpFromEmail}
                        onChange={(event) => setSmtpFromEmail(event.target.value)}
                    />
                </label>
                <label className="flex items-center gap-2 md:col-span-2">
                    <input
                        aria-label={smtpUseStartTlsText}
                        type="checkbox"
                        checked={smtpUseTls}
                        onChange={(event) => setSmtpUseTls(event.target.checked)}
                    />
                    <span className="text-sm text-gray-700">{smtpUseStartTlsText}</span>
                </label>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-3">
                <button
                    type="button"
                    className="rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-100"
                    onClick={onCheckEmailSettings}
                    disabled={smtpCheckLoading}
                >
                    {smtpCheckLoading ? checkingEmailSettingsText : checkEmailSettingsText}
                </button>
                {smtpCheckMessage && <p className="text-sm text-green-700">{smtpCheckMessage}</p>}
                {smtpCheckError && <p className="text-sm text-red-700">{smtpCheckError}</p>}
            </div>
        </div>
    );
}

export function AuthBaseUrlsSection({
    authBaseUrlsTitleText,
    authBaseUrlsHintText,
    authFrontendBaseUrlText,
    authFrontendBaseUrl,
    setAuthFrontendBaseUrl,
    authBackendBaseUrlText,
    authBackendBaseUrl,
    setAuthBackendBaseUrl,
}: AuthBaseUrlsSectionProps) {
    return (
        <div className="rounded border border-slate-200 bg-slate-50 p-4">
            <h2 className="mb-1 text-sm font-semibold text-gray-800">{authBaseUrlsTitleText}</h2>
            <p className="mb-3 text-xs text-gray-600">{authBaseUrlsHintText}</p>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{authFrontendBaseUrlText}</span>
                    <input
                        aria-label={authFrontendBaseUrlText}
                        type="url"
                        className="ace-input"
                        value={authFrontendBaseUrl}
                        onChange={(event) => setAuthFrontendBaseUrl(event.target.value)}
                    />
                </label>
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{authBackendBaseUrlText}</span>
                    <input
                        aria-label={authBackendBaseUrlText}
                        type="url"
                        className="ace-input"
                        value={authBackendBaseUrl}
                        onChange={(event) => setAuthBackendBaseUrl(event.target.value)}
                    />
                </label>
            </div>
        </div>
    );
}

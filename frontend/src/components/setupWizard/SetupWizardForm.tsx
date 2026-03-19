import type {useSetupWizardForm} from "./useSetupWizardForm";

type SetupWizardFormProps = {
    form: ReturnType<typeof useSetupWizardForm>;
};

function FieldError({message}: {message?: string}) {
    if (!message) {
        return null;
    }

    return <p className="mt-1 text-xs text-red-700">{message}</p>;
}

export function SetupWizardForm({form}: SetupWizardFormProps) {
    const {
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
    } = form;

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <form onSubmit={onSubmit} className="ace-card ace-card-strong ace-card-pad w-full max-w-3xl">
                <h1 className="text-2xl font-semibold text-gray-900">{copy.title}</h1>
                <p className="mb-6 mt-2 text-sm text-gray-600">{copy.subtitle}</p>

                {formError && (
                    <div role="alert" className="mb-4 rounded-md border border-red-300 bg-red-50 p-3 text-red-800">
                        {formError}
                    </div>
                )}

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <label className="block">
                        <span className="ace-field-label">{copy.initialSetupToken}</span>
                        <input type="password" value={setupToken} onChange={(e) => setSetupToken(e.target.value)} className="ace-input" />
                        <FieldError message={fieldErrors.setup_token} />
                    </label>

                    <label className="block">
                        <span className="ace-field-label">{copy.siteName}</span>
                        <input type="text" value={siteName} onChange={(e) => setSiteName(e.target.value)} className="ace-input" />
                        <FieldError message={fieldErrors.site_name} />
                    </label>

                    <label className="block md:col-span-2">
                        <span className="ace-field-label">{copy.supportedLocales}</span>
                        <input type="text" value={supportedLocalesRaw} readOnly className="ace-input" />
                        <p className="mt-1 text-xs text-gray-500">{copy.localesHint}</p>
                        <FieldError message={fieldErrors.supported_locales} />
                    </label>

                    <label className="block">
                        <span className="ace-field-label">{copy.adminEmail}</span>
                        <input type="email" value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} className="ace-input" />
                        <FieldError message={fieldErrors.admin_email} />
                    </label>

                    <label className="block">
                        <span className="ace-field-label">{copy.adminPassword}</span>
                        <input type="password" value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} className="ace-input" />
                        <FieldError message={fieldErrors.admin_password} />
                    </label>
                </div>

                <div className="mt-6 rounded-lg border border-gray-200 p-4">
                    <h2 className="text-lg font-semibold text-gray-900">{copy.optionalEmailSettings}</h2>
                    <p className="mt-1 text-sm text-gray-600">{copy.optionalEmailSettingsHint}</p>
                    <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
                        <label className="block">
                            <span className="ace-field-label">{copy.smtpHost}</span>
                            <input type="text" value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)} className="ace-input" />
                            <FieldError message={fieldErrors.smtp_host} />
                        </label>
                        <label className="block">
                            <span className="ace-field-label">{copy.smtpPort}</span>
                            <input type="number" value={smtpPort} onChange={(e) => setSmtpPort(e.target.value)} className="ace-input" />
                            <FieldError message={fieldErrors.smtp_port} />
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
                            <FieldError message={fieldErrors.smtp_from_email} />
                        </label>
                        <label className="flex items-center gap-2 md:col-span-2">
                            <input type="checkbox" checked={smtpUseTls} onChange={(e) => setSmtpUseTls(e.target.checked)} />
                            <span className="text-sm text-gray-700">{copy.smtpUseStartTls}</span>
                        </label>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-3">
                        <button
                            type="button"
                            onClick={onCheckEmailSettings}
                            className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
                            disabled={smtpCheckState.loading}
                        >
                            {smtpCheckState.loading ? copy.checkingEmailSettings : copy.checkEmailSettings}
                        </button>
                        {smtpCheckState.message && <p className="text-sm text-green-700">{smtpCheckState.message}</p>}
                        {smtpCheckState.error && <p className="text-sm text-red-700">{smtpCheckState.error}</p>}
                    </div>
                </div>

                <div className="mt-6 rounded-lg border border-gray-200 p-4">
                    <h2 className="text-lg font-semibold text-gray-900">{copy.authBaseUrls}</h2>
                    <p className="mt-1 text-sm text-gray-600">{copy.authBaseUrlsHint}</p>
                    <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
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

                <button type="submit" disabled={isSubmitting} className="ace-primary-btn mt-6 py-2.5">
                    {isSubmitting ? copy.initializing : copy.initialize}
                </button>
            </form>
        </div>
    );
}

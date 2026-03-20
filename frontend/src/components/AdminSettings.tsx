import {useMemo} from "react";
import {Navigate} from "react-router-dom";

import {
    AiKeysSection,
    BrandingSection,
    LocaleAdminSection,
} from "./adminSettings/AdminSettingsPrimarySections.tsx";
import {
    AuthBaseUrlsSection,
    EmailSettingsSection,
} from "./adminSettings/AdminSettingsSecondarySections.tsx";
import {useAdminSettingsForm} from "./adminSettings/useAdminSettingsForm.ts";
import {useAdminSettingsText} from "./adminSettings/useAdminSettingsText.ts";
import {resolveAdminSettingsLocale} from "./adminSettings/adminSettingsUtils.ts";

export default function AdminSettings() {
    const pageLocale = useMemo(resolveAdminSettingsLocale, []);
    const text = useAdminSettingsText(pageLocale);
    const form = useAdminSettingsForm(text);
    const {
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
    } = form;
    const {
        titleText,
        aiKeysText,
        openAiKeyText,
        deepSeekKeyText,
        siteLogoText,
        backgroundImageText,
        saveText,
        savingText,
        loadingText,
        siteLogoPreviewAltText,
        backgroundPreviewAltText,
        translationWarningMissingKeysText,
        translationWarningAutoText,
        emailSettingsTitleText,
        emailEnabledStatusText,
        emailDisabledStatusText,
        smtpHostText,
        smtpPortText,
        smtpUsernameText,
        smtpPasswordText,
        smtpFromEmailText,
        smtpUseStartTlsText,
        authFrontendBaseUrlText,
        authBackendBaseUrlText,
        authBaseUrlsTitleText,
        authBaseUrlsHintText,
        checkEmailSettingsText,
        checkingEmailSettingsText,
        siteNameText,
        supportedLocalesText,
        supportedLocalesHintText,
        adminEmailText,
        adminPasswordText,
    } = text;

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
                        <BrandingSection
                            siteNameText={siteNameText}
                            siteName={siteName}
                            setSiteName={setSiteName}
                            siteLogoText={siteLogoText}
                            siteLogo={siteLogo}
                            siteLogoPreviewAltText={siteLogoPreviewAltText}
                            handleLogoChange={handleLogoChange}
                            backgroundImageText={backgroundImageText}
                            backgroundImage={backgroundImage}
                            backgroundPreviewAltText={backgroundPreviewAltText}
                            handleBackgroundChange={handleBackgroundChange}
                        />
                        <LocaleAdminSection
                            supportedLocalesText={supportedLocalesText}
                            supportedLocalesRaw={supportedLocalesRaw}
                            setSupportedLocalesRaw={setSupportedLocalesRaw}
                            supportedLocalesHintText={supportedLocalesHintText}
                            adminEmailText={adminEmailText}
                            adminEmail={adminEmail}
                            setAdminEmail={setAdminEmail}
                            adminPasswordText={adminPasswordText}
                            adminPassword={adminPassword}
                            adminPasswordDirty={adminPasswordDirty}
                            setAdminPassword={setAdminPassword}
                            setAdminPasswordDirty={setAdminPasswordDirty}
                        />
                        <AiKeysSection
                            aiKeysText={aiKeysText}
                            openAiKeyText={openAiKeyText}
                            openAiKey={openAiKey}
                            setOpenAiKey={setOpenAiKey}
                            setOpenAiKeyDirty={setOpenAiKeyDirty}
                            deepSeekKeyText={deepSeekKeyText}
                            deepSeekKey={deepSeekKey}
                            setDeepSeekKey={setDeepSeekKey}
                            setDeepSeekKeyDirty={setDeepSeekKeyDirty}
                            hasAiKeyConfigured={hasAiKeyConfigured}
                            translationWarningMissingKeysText={translationWarningMissingKeysText}
                            translationWarningAutoText={translationWarningAutoText}
                        />
                        <EmailSettingsSection
                            emailSettingsTitleText={emailSettingsTitleText}
                            emailConfigured={emailConfigured}
                            emailEnabledStatusText={emailEnabledStatusText}
                            emailDisabledStatusText={emailDisabledStatusText}
                            smtpHostText={smtpHostText}
                            smtpHost={smtpHost}
                            setSmtpHost={setSmtpHost}
                            smtpPortText={smtpPortText}
                            smtpPort={smtpPort}
                            setSmtpPort={setSmtpPort}
                            smtpUsernameText={smtpUsernameText}
                            smtpUsername={smtpUsername}
                            setSmtpUsername={setSmtpUsername}
                            smtpPasswordText={smtpPasswordText}
                            smtpPassword={smtpPassword}
                            smtpPasswordDirty={smtpPasswordDirty}
                            setSmtpPassword={setSmtpPassword}
                            setSmtpPasswordDirty={setSmtpPasswordDirty}
                            smtpFromEmailText={smtpFromEmailText}
                            smtpFromEmail={smtpFromEmail}
                            setSmtpFromEmail={setSmtpFromEmail}
                            smtpUseTls={smtpUseTls}
                            setSmtpUseTls={setSmtpUseTls}
                            smtpUseStartTlsText={smtpUseStartTlsText}
                            onCheckEmailSettings={onCheckEmailSettings}
                            smtpCheckLoading={smtpCheckLoading}
                            checkEmailSettingsText={checkEmailSettingsText}
                            checkingEmailSettingsText={checkingEmailSettingsText}
                            smtpCheckMessage={smtpCheckMessage}
                            smtpCheckError={smtpCheckError}
                        />
                        <AuthBaseUrlsSection
                            authBaseUrlsTitleText={authBaseUrlsTitleText}
                            authBaseUrlsHintText={authBaseUrlsHintText}
                            authFrontendBaseUrlText={authFrontendBaseUrlText}
                            authFrontendBaseUrl={authFrontendBaseUrl}
                            setAuthFrontendBaseUrl={setAuthFrontendBaseUrl}
                            authBackendBaseUrlText={authBackendBaseUrlText}
                            authBackendBaseUrl={authBackendBaseUrl}
                            setAuthBackendBaseUrl={setAuthBackendBaseUrl}
                        />
                    </div>

                    <button type="submit" disabled={saving} className="rounded bg-blue-700 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:bg-gray-400">
                        {saving ? savingText : saveText}
                    </button>
                </form>
            </div>
        </div>
    );
}

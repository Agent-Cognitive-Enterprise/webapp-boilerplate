import {useMemo} from "react";
import {Navigate} from "react-router-dom";

import {useAdminSettingsForm} from "./adminSettings/useAdminSettingsForm.ts";
import {useAdminSettingsText} from "./adminSettings/useAdminSettingsText.ts";
import {EXISTING_SECRET_PLACEHOLDER, resolveAdminSettingsLocale} from "./adminSettings/adminSettingsUtils.ts";

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

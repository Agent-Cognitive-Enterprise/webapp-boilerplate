import type {ChangeEvent} from "react";

type BrandingSectionProps = {
    siteNameText: string;
    siteName: string;
    setSiteName: (value: string) => void;
    siteLogoText: string;
    siteLogo: string | null;
    siteLogoPreviewAltText: string;
    handleLogoChange: (event: ChangeEvent<HTMLInputElement>) => void | Promise<void>;
    backgroundImageText: string;
    backgroundImage: string | null;
    backgroundPreviewAltText: string;
    handleBackgroundChange: (event: ChangeEvent<HTMLInputElement>) => void | Promise<void>;
};

type LocaleAdminSectionProps = {
    supportedLocalesText: string;
    supportedLocalesRaw: string;
    setSupportedLocalesRaw: (value: string) => void;
    supportedLocalesHintText: string;
    adminEmailText: string;
    adminEmail: string;
    setAdminEmail: (value: string) => void;
    adminPasswordText: string;
    adminPassword: string;
    adminPasswordDirty: boolean;
    setAdminPassword: (value: string) => void;
    setAdminPasswordDirty: (value: boolean) => void;
};

type AiKeysSectionProps = {
    aiKeysText: string;
    openAiKeyText: string;
    openAiKey: string;
    setOpenAiKey: (value: string) => void;
    setOpenAiKeyDirty: (value: boolean) => void;
    deepSeekKeyText: string;
    deepSeekKey: string;
    setDeepSeekKey: (value: string) => void;
    setDeepSeekKeyDirty: (value: boolean) => void;
    hasAiKeyConfigured: boolean;
    translationWarningMissingKeysText: string;
    translationWarningAutoText: string;
};

export function BrandingSection({
    siteNameText,
    siteName,
    setSiteName,
    siteLogoText,
    siteLogo,
    siteLogoPreviewAltText,
    handleLogoChange,
    backgroundImageText,
    backgroundImage,
    backgroundPreviewAltText,
    handleBackgroundChange,
}: BrandingSectionProps) {
    return (
        <>
            <label className="block">
                <span className="text-sm font-medium text-gray-700">{siteNameText}</span>
                <input
                    aria-label={siteNameText}
                    className="ace-input"
                    value={siteName}
                    onChange={(event) => setSiteName(event.target.value)}
                />
            </label>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{siteLogoText}</span>
                    <input
                        aria-label={siteLogoText}
                        type="file"
                        accept="image/*"
                        className="ace-input"
                        onChange={handleLogoChange}
                    />
                    {siteLogo && (
                        <img
                            src={siteLogo}
                            alt={siteLogoPreviewAltText}
                            className="mt-2 max-h-24 rounded border p-2 object-contain"
                        />
                    )}
                </label>
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{backgroundImageText}</span>
                    <input
                        aria-label={backgroundImageText}
                        type="file"
                        accept="image/*"
                        className="ace-input"
                        onChange={handleBackgroundChange}
                    />
                    {backgroundImage && (
                        <img
                            src={backgroundImage}
                            alt={backgroundPreviewAltText}
                            className="mt-2 max-h-24 rounded border object-cover"
                        />
                    )}
                </label>
            </div>
        </>
    );
}

export function LocaleAdminSection({
    supportedLocalesText,
    supportedLocalesRaw,
    setSupportedLocalesRaw,
    supportedLocalesHintText,
    adminEmailText,
    adminEmail,
    setAdminEmail,
    adminPasswordText,
    adminPassword,
    adminPasswordDirty,
    setAdminPassword,
    setAdminPasswordDirty,
}: LocaleAdminSectionProps) {
    return (
        <>
            <label className="block w-full">
                <span className="text-sm font-medium text-gray-700">{supportedLocalesText}</span>
                <input
                    aria-label={supportedLocalesText}
                    className="ace-input"
                    value={supportedLocalesRaw}
                    onChange={(event) => setSupportedLocalesRaw(event.target.value)}
                />
                <p className="mt-1 text-xs text-gray-500">{supportedLocalesHintText}</p>
            </label>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{adminEmailText}</span>
                    <input
                        aria-label={adminEmailText}
                        type="email"
                        className="ace-input"
                        value={adminEmail}
                        onChange={(event) => setAdminEmail(event.target.value)}
                    />
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
                        onChange={(event) => {
                            setAdminPasswordDirty(true);
                            setAdminPassword(event.target.value);
                        }}
                    />
                </label>
            </div>
        </>
    );
}

export function AiKeysSection({
    aiKeysText,
    openAiKeyText,
    openAiKey,
    setOpenAiKey,
    setOpenAiKeyDirty,
    deepSeekKeyText,
    deepSeekKey,
    setDeepSeekKey,
    setDeepSeekKeyDirty,
    hasAiKeyConfigured,
    translationWarningMissingKeysText,
    translationWarningAutoText,
}: AiKeysSectionProps) {
    return (
        <div className="rounded border border-slate-200 bg-slate-50 p-4">
            <h2 className="mb-3 text-sm font-semibold text-gray-800">{aiKeysText}</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="block">
                    <span className="text-sm font-medium text-gray-700">{openAiKeyText}</span>
                    <input
                        aria-label={openAiKeyText}
                        type="password"
                        autoComplete="off"
                        className="ace-input"
                        value={openAiKey}
                        onChange={(event) => {
                            setOpenAiKeyDirty(true);
                            setOpenAiKey(event.target.value);
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
                        onChange={(event) => {
                            setDeepSeekKeyDirty(true);
                            setDeepSeekKey(event.target.value);
                        }}
                    />
                </label>
            </div>
            <div
                className={`mt-3 rounded border px-3 py-2 text-xs ${
                    hasAiKeyConfigured
                        ? "border-blue-200 bg-blue-50 text-blue-800"
                        : "border-amber-200 bg-amber-50 text-amber-800"
                }`}
            >
                {!hasAiKeyConfigured && <p>{translationWarningMissingKeysText}</p>}
                <p>{translationWarningAutoText}</p>
            </div>
        </div>
    );
}

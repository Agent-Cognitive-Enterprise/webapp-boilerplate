import { useEffect, useState } from "react";

import { getSetupStatus } from "../api/setup.ts";
import { resolveSetupLocale, SETUP_SUPPORTED_LOCALES } from "../i18n/setupLocaleMeta.ts";
import { applyDocumentLocaleDirection, getActiveUiLocale } from "../i18n/localeDirection.ts";
import { getPreferredUiLocale } from "../i18n/uiLocale.ts";

const DEFAULT_SETUP_COPY = {
    checkingSetupStatus: "Checking setup status...",
    backendOfflineTitle: "Backend is offline",
    backendOfflineDescription: "Cannot reach backend service. Start backend and refresh this page.",
};

type SetupEmailDefaults = {
    smtp_host?: string | null;
    smtp_port?: number | null;
    smtp_username?: string | null;
    smtp_password?: string | null;
    smtp_from_email?: string | null;
    smtp_use_tls?: boolean;
    auth_frontend_base_url?: string | null;
    auth_backend_base_url?: string | null;
} | null;

type SetupCopy = typeof DEFAULT_SETUP_COPY;

export type UseSetupBootstrapResult = {
    setupLoading: boolean;
    isInitialized: boolean;
    seedLocales: string[];
    setupEmailDefaults: SetupEmailDefaults;
    setupCopy: SetupCopy;
    setIsInitialized: (value: boolean) => void;
};

export function useSetupBootstrap(): UseSetupBootstrapResult {
    const [setupLoading, setSetupLoading] = useState(true);
    const [isInitialized, setIsInitialized] = useState(false);
    const [seedLocales, setSeedLocales] = useState<string[]>([...SETUP_SUPPORTED_LOCALES]);
    const [setupEmailDefaults, setSetupEmailDefaults] = useState<SetupEmailDefaults>(null);
    const [setupCopy, setSetupCopy] = useState(DEFAULT_SETUP_COPY);

    const setupLocale = resolveSetupLocale(getPreferredUiLocale()) ?? "en";

    useEffect(() => {
        applyDocumentLocaleDirection(getActiveUiLocale());
    }, []);

    useEffect(() => {
        let active = true;
        void import("../i18n/setupWizardLocales.ts").then((module) => {
            if (!active) {
                return;
            }
            const copy = module.getSetupCopy(setupLocale);
            setSetupCopy({
                checkingSetupStatus: copy.checkingSetupStatus,
                backendOfflineTitle: copy.backendOfflineTitle,
                backendOfflineDescription: copy.backendOfflineDescription,
            });
        });
        return () => {
            active = false;
        };
    }, [setupLocale]);

    useEffect(() => {
        let active = true;
        async function loadStatus() {
            try {
                const status = await getSetupStatus();
                if (!active) return;
                setIsInitialized(status.is_initialized);
                if (Array.isArray(status.seed_locales) && status.seed_locales.length > 0) {
                    setSeedLocales(status.seed_locales);
                }
                setSetupEmailDefaults(status.email_defaults ?? null);
            } catch {
                if (!active) return;
                setIsInitialized(false);
            } finally {
                if (active) setSetupLoading(false);
            }
        }

        void loadStatus();
        return () => {
            active = false;
        };
    }, []);

    return {
        setupLoading,
        isInitialized,
        seedLocales,
        setupEmailDefaults,
        setupCopy,
        setIsInitialized,
    };
}

export { DEFAULT_SETUP_COPY };

// /frontend/src/App.tsx
// noinspection SpellCheckingInspection

import {
    Routes,
    Route,
    Link,
    Navigate,
    useLocation,
} from "react-router-dom";
import RequireAuth from "./components/RequireAuth.tsx";
import {lazy, Suspense, useContext, useEffect, useState} from "react";
import {AuthContext} from "./contexts/AuthContext.tsx";
import {useKeepUserLoggedIn} from "./hooks/useKeepUserLoggedIn.ts";
import UiLabel from "./components/UiLabel.tsx";
import {getSetupStatus} from "./api/setup.ts";
import {fetchPublicBranding} from "./api/appConfig.ts";
import {useT} from "./hooks/useT.ts";
import {
    resolveSetupLocale,
    SETUP_SUPPORTED_LOCALES,
} from "./i18n/setupLocaleMeta.ts";
import {
    applyDocumentLocaleDirection,
    getActiveUiLocale,
} from "./i18n/localeDirection.ts";
import backgroundImage from "./assets/beach-4455224_1920.jpg";
import mobileBackgroundImage from "./assets/beach-4455224_mobile_720x1280.jpg";

const Register = lazy(() => import("./components/Register.tsx"));
const Login = lazy(() => import("./components/Login.tsx"));
const SetupWizard = lazy(() => import("./components/SetupWizard.tsx"));
const UserProfile = lazy(() => import("./components/UserProfile.tsx"));
const Dashboard = lazy(() => import("./components/Dashboard.tsx"));
const UserManagement = lazy(() => import("./components/UserManagement.tsx"));
const ForgotPassword = lazy(() => import("./components/ForgotPassword.tsx"));
const ResetPassword = lazy(() => import("./components/ResetPassword.tsx"));
const AdminSettings = lazy(() => import("./components/AdminSettings.tsx"));

const HEALTH_CHECK_INTERVAL_MS = 10000;
const HEALTH_CHECK_TIMEOUT_MS = 5000;
const BRANDING_BG_STORAGE_KEY = "branding.backgroundImage";
const BRANDING_LOGO_STORAGE_KEY = "branding.siteLogo";
const MOBILE_VIEWPORT_QUERY = "(max-width: 767px)";
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

function readStoredBranding(key: string): string | null {
    const value = localStorage.getItem(key);
    if (!value || value.trim().length === 0) {
        return null;
    }
    return value;
}

function getDefaultBackgroundForViewport(isMobileViewport: boolean): string {
    return isMobileViewport ? mobileBackgroundImage : backgroundImage;
}

function isMobileViewport(): boolean {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
        return false;
    }
    return window.matchMedia(MOBILE_VIEWPORT_QUERY).matches;
}

function InitializedApp() {
    const auth = useContext(AuthContext);
    const location = useLocation();
    const [siteLogo, setSiteLogo] = useState<string | null>(() => readStoredBranding(BRANDING_LOGO_STORAGE_KEY));
    const [brandingBackgroundUrl, setBrandingBackgroundUrl] = useState<string | null>(() => readStoredBranding(BRANDING_BG_STORAGE_KEY));
    const [mobileViewport, setMobileViewport] = useState<boolean>(() => isMobileViewport());
    const [mobileNavOpen, setMobileNavOpen] = useState(false);
    const siteLogoAltText = useT("app.alt.site_logo", undefined, "Site logo");

    useKeepUserLoggedIn(); // Keep the session alive by polling the profile every 180 seconds

    useEffect(() => {
        let active = true;
        async function loadBranding() {
            try {
                const branding = await fetchPublicBranding();
                if (!active) return;
                setSiteLogo(branding.siteLogo);
                if (branding.siteLogo) {
                    localStorage.setItem(BRANDING_LOGO_STORAGE_KEY, branding.siteLogo);
                } else {
                    localStorage.removeItem(BRANDING_LOGO_STORAGE_KEY);
                }
                if (branding.backgroundImage) {
                    setBrandingBackgroundUrl(branding.backgroundImage);
                    localStorage.setItem(BRANDING_BG_STORAGE_KEY, branding.backgroundImage);
                } else {
                    setBrandingBackgroundUrl(null);
                    localStorage.removeItem(BRANDING_BG_STORAGE_KEY);
                }
            } catch {
                if (!active) return;
            }
        }
        void loadBranding();
        return () => {
            active = false;
        };
    }, []);

    useEffect(() => {
        setMobileNavOpen(false);
    }, [auth?.token, location.pathname]);

    useEffect(() => {
        if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
            return;
        }
        const mediaQuery = window.matchMedia(MOBILE_VIEWPORT_QUERY);
        const onChange = (event: MediaQueryListEvent) => setMobileViewport(event.matches);
        setMobileViewport(mediaQuery.matches);
        if (typeof mediaQuery.addEventListener === "function") {
            mediaQuery.addEventListener("change", onChange);
            return () => mediaQuery.removeEventListener("change", onChange);
        }
        mediaQuery.addListener(onChange);
        return () => mediaQuery.removeListener(onChange);
    }, []);

    const isAdmin = Boolean(auth?.user?.is_admin);
    const backgroundUrl = brandingBackgroundUrl ?? getDefaultBackgroundForViewport(mobileViewport);

    return (
        <div
            data-testid="app-background-shell"
            className="relative min-h-screen w-full bg-center bg-cover overflow-hidden"
            style={backgroundUrl ? {backgroundImage: `url(${backgroundUrl})`} : undefined}
        >
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-slate-950/30 via-slate-900/15 to-slate-900/40"/>
            <nav
                className="fixed top-0 left-0 w-full border-b border-white/20 bg-slate-900/70 backdrop-blur-md shadow z-50"
            >
                <div className="mx-auto max-w-7xl px-4 py-3 md:px-6">
                    <div className="flex items-center justify-between gap-3">
                        <div className="flex min-w-0 items-center gap-2">
                            {siteLogo && (
                                <img src={siteLogo} alt={siteLogoAltText} className="h-8 w-auto max-w-32 object-contain md:max-w-40"/>
                            )}
                        </div>

                        <button
                            type="button"
                            onClick={() => setMobileNavOpen((prev) => !prev)}
                            className="rounded-md border border-white/30 px-3 py-1.5 text-sm font-semibold text-white md:hidden"
                            aria-expanded={mobileNavOpen}
                            aria-label="Toggle navigation menu"
                        >
                            {mobileNavOpen ? "Close" : "Menu"}
                        </button>

                        <ul className="hidden items-center gap-1 md:flex">
                            {!auth?.token && (
                                <>
                                    <li><Link to="/register" className="ace-nav-link"><UiLabel k="nav.title.register"/></Link></li>
                                    <li><Link to="/login" className="ace-nav-link"><UiLabel k="nav.title.login"/></Link></li>
                                </>
                            )}
                            {auth?.token && (
                                <>
                                    <li><Link to="/dashboard" className="ace-nav-link"><UiLabel k="nav.title.dashboard"/></Link></li>
                                    <li><Link to="/profile" className="ace-nav-link"><UiLabel k="nav.title.profile"/></Link></li>
                                    {isAdmin && <li><Link to="/users" className="ace-nav-link"><UiLabel k="nav.title.users"/></Link></li>}
                                    {isAdmin && <li><Link to="/admin/settings" className="ace-nav-link"><UiLabel k="nav.title.admin_settings"/></Link></li>}
                                    <li>
                                        <button onClick={auth.logout} className="ace-nav-button">
                                            <UiLabel k="nav.title.logout"/>
                                        </button>
                                    </li>
                                </>
                            )}
                        </ul>
                    </div>

                    {mobileNavOpen && (
                        <ul className="mt-3 grid grid-cols-1 gap-2 md:hidden">
                            {!auth?.token && (
                                <>
                                    <li><Link to="/register" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.register"/></Link></li>
                                    <li><Link to="/login" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.login"/></Link></li>
                                </>
                            )}
                            {auth?.token && (
                                <>
                                    <li><Link to="/dashboard" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.dashboard"/></Link></li>
                                    <li><Link to="/profile" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.profile"/></Link></li>
                                    {isAdmin && <li><Link to="/users" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.users"/></Link></li>}
                                    {isAdmin && <li><Link to="/admin/settings" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.admin_settings"/></Link></li>}
                                    <li>
                                        <button
                                            onClick={auth.logout}
                                            className="ace-nav-button w-full justify-center"
                                        >
                                            <UiLabel k="nav.title.logout"/>
                                        </button>
                                    </li>
                                </>
                            )}
                        </ul>
                    )}
                </div>
            </nav>

            <main className="relative z-10">
                <Suspense fallback={<div className="min-h-[40vh]" />}>
                <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace/>}/>
                <Route
                    path="/setup"
                    element={
                        <SetupWizard
                            isInitialized={true}
                            onSetupComplete={() => undefined}
                            seedLocales={[...SETUP_SUPPORTED_LOCALES]}
                        />
                    }
                />
                <Route path="/register" element={<Register/>}/>
                <Route path="/login" element={<Login/>}/>
                <Route path="/forgot-password" element={<ForgotPassword/>}/>
                <Route path="/reset-password" element={<ResetPassword/>}/>
                <Route path="/dashboard" element={
                    <RequireAuth>
                        <Dashboard/>
                    </RequireAuth>
                }/>
                <Route path="/profile" element={
                    <RequireAuth>
                        <UserProfile/>
                    </RequireAuth>
                }/>
                <Route path="/users" element={
                    <RequireAuth>
                        <UserManagement/>
                    </RequireAuth>
                }/>
                <Route path="/admin/settings" element={
                    <RequireAuth>
                        <AdminSettings/>
                    </RequireAuth>
                }/>
                </Routes>
                </Suspense>
            </main>
        </div>
    );
}

export default function App() {
    const location = useLocation();
    const [setupLoading, setSetupLoading] = useState(true);
    const [isInitialized, setIsInitialized] = useState(false);
    const [backendOffline, setBackendOffline] = useState(false);
    const [seedLocales, setSeedLocales] = useState<string[]>([...SETUP_SUPPORTED_LOCALES]);
    const [setupEmailDefaults, setSetupEmailDefaults] = useState<SetupEmailDefaults>(null);
    const [setupCopy, setSetupCopy] = useState(DEFAULT_SETUP_COPY);

    const setupLocale = resolveSetupLocale(localStorage.getItem("uiLocale") || navigator.language || "en") ?? "en";

    useEffect(() => {
        applyDocumentLocaleDirection(getActiveUiLocale());
    }, []);

    useEffect(() => {
        let active = true;
        void import("./i18n/setupWizardLocales.ts").then((module) => {
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

    async function probeBackendHealth(): Promise<boolean> {
        const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), HEALTH_CHECK_TIMEOUT_MS);
        try {
            const response = await fetch(`${baseUrl}/health`, {
                method: "GET",
                signal: controller.signal,
            });
            return response.ok;
        } catch {
            return false;
        } finally {
            window.clearTimeout(timeout);
        }
    }

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
                setBackendOffline(false);
            } catch {
                if (!active) return;
                setIsInitialized(false);
                setBackendOffline(true);
            } finally {
                if (active) setSetupLoading(false);
            }
        }

        void loadStatus();
        return () => {
            active = false;
        };
    }, []);

    useEffect(() => {
        let active = true;

        async function runProbe() {
            if (typeof document !== "undefined" && document.visibilityState === "hidden") {
                return;
            }
            const online = await probeBackendHealth();
            if (!active) return;
            setBackendOffline(!online);
        }

        void runProbe();
        const intervalId = window.setInterval(() => {
            void runProbe();
        }, HEALTH_CHECK_INTERVAL_MS);

        return () => {
            active = false;
            window.clearInterval(intervalId);
        };
    }, []);

    const offlineOverlay = backendOffline && (
        <div className="fixed inset-0 z-[100] bg-black/55 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="w-full max-w-lg rounded-lg bg-white shadow-2xl p-6 border border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">{setupCopy.backendOfflineTitle}</h2>
                <p className="mt-2 text-gray-700">{setupCopy.backendOfflineDescription}</p>
            </div>
        </div>
    );

    if (setupLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-700">
                {setupCopy.checkingSetupStatus}
            </div>
        );
    }

    if (!isInitialized) {
        return (
            <div className="relative min-h-screen">
                <Suspense fallback={<div className="min-h-[40vh]" />}>
                    <Routes>
                        <Route
                            path="/setup"
                            element={
                                <SetupWizard
                                    isInitialized={false}
                                    onSetupComplete={() => setIsInitialized(true)}
                                    seedLocales={seedLocales}
                                    emailDefaults={setupEmailDefaults}
                                />
                            }
                        />
                        <Route path="*" element={<Navigate to="/setup" replace/>}/>
                    </Routes>
                </Suspense>
                {offlineOverlay}
            </div>
        );
    }

    if (isInitialized && location.pathname === "/setup") {
        return (
            <Suspense fallback={<div className="min-h-[40vh]" />}>
                <SetupWizard isInitialized={true} onSetupComplete={() => undefined} seedLocales={seedLocales}/>
            </Suspense>
        );
    }

    return (
        <div className="relative min-h-screen">
            <InitializedApp/>
            {offlineOverlay}
        </div>
    );
}

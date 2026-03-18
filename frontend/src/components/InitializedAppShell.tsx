import { lazy, Suspense, useContext, useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { fetchPublicBranding } from "../api/appConfig.ts";
import backgroundImage from "../assets/beach-4455224_1920.jpg";
import mobileBackgroundImage from "../assets/beach-4455224_mobile_720x1280.jpg";
import UiLabel from "./UiLabel.tsx";
import RequireAuth from "./RequireAuth.tsx";
import { AuthContext } from "../contexts/AuthContext.tsx";
import { useKeepUserLoggedIn } from "../hooks/useKeepUserLoggedIn.ts";
import { useT } from "../hooks/useT.ts";
import { SETUP_SUPPORTED_LOCALES } from "../i18n/setupLocaleMeta.ts";

const Register = lazy(() => import("./Register.tsx"));
const Login = lazy(() => import("./Login.tsx"));
const SetupWizard = lazy(() => import("./SetupWizard.tsx"));
const UserProfile = lazy(() => import("./UserProfile.tsx"));
const Dashboard = lazy(() => import("./Dashboard.tsx"));
const UserManagement = lazy(() => import("./UserManagement.tsx"));
const ForgotPassword = lazy(() => import("./ForgotPassword.tsx"));
const ResetPassword = lazy(() => import("./ResetPassword.tsx"));
const AdminSettings = lazy(() => import("./AdminSettings.tsx"));

const BRANDING_BG_STORAGE_KEY = "branding.backgroundImage";
const BRANDING_LOGO_STORAGE_KEY = "branding.siteLogo";
const MOBILE_VIEWPORT_QUERY = "(max-width: 767px)";

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

export default function InitializedAppShell() {
    const auth = useContext(AuthContext);
    const location = useLocation();
    const [siteLogo, setSiteLogo] = useState<string | null>(() => readStoredBranding(BRANDING_LOGO_STORAGE_KEY));
    const [brandingBackgroundUrl, setBrandingBackgroundUrl] = useState<string | null>(() =>
        readStoredBranding(BRANDING_BG_STORAGE_KEY)
    );
    const [mobileViewport, setMobileViewport] = useState<boolean>(() => isMobileViewport());
    const [mobileNavOpen, setMobileNavOpen] = useState(false);
    const siteLogoAltText = useT("app.alt.site_logo", undefined, "Site logo");

    useKeepUserLoggedIn();

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
            className="relative min-h-screen w-full overflow-hidden bg-cover bg-center"
            style={backgroundUrl ? { backgroundImage: `url(${backgroundUrl})` } : undefined}
        >
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-slate-950/30 via-slate-900/15 to-slate-900/40" />
            <nav className="fixed top-0 left-0 z-50 w-full border-b border-white/20 bg-slate-900/70 shadow backdrop-blur-md">
                <div className="mx-auto max-w-7xl px-4 py-3 md:px-6">
                    <div className="flex items-center justify-between gap-3">
                        <div className="flex min-w-0 items-center gap-2">
                            {siteLogo && (
                                <img
                                    src={siteLogo}
                                    alt={siteLogoAltText}
                                    className="h-8 w-auto max-w-32 object-contain md:max-w-40"
                                />
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
                                    <li><Link to="/register" className="ace-nav-link"><UiLabel k="nav.title.register" /></Link></li>
                                    <li><Link to="/login" className="ace-nav-link"><UiLabel k="nav.title.login" /></Link></li>
                                </>
                            )}
                            {auth?.token && (
                                <>
                                    <li><Link to="/dashboard" className="ace-nav-link"><UiLabel k="nav.title.dashboard" /></Link></li>
                                    <li><Link to="/profile" className="ace-nav-link"><UiLabel k="nav.title.profile" /></Link></li>
                                    {isAdmin && <li><Link to="/users" className="ace-nav-link"><UiLabel k="nav.title.users" /></Link></li>}
                                    {isAdmin && (
                                        <li><Link to="/admin/settings" className="ace-nav-link"><UiLabel k="nav.title.admin_settings" /></Link></li>
                                    )}
                                    <li>
                                        <button onClick={auth.logout} className="ace-nav-button">
                                            <UiLabel k="nav.title.logout" />
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
                                    <li><Link to="/register" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.register" /></Link></li>
                                    <li><Link to="/login" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.login" /></Link></li>
                                </>
                            )}
                            {auth?.token && (
                                <>
                                    <li><Link to="/dashboard" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.dashboard" /></Link></li>
                                    <li><Link to="/profile" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.profile" /></Link></li>
                                    {isAdmin && <li><Link to="/users" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.users" /></Link></li>}
                                    {isAdmin && (
                                        <li><Link to="/admin/settings" className="ace-nav-link w-full justify-center"><UiLabel k="nav.title.admin_settings" /></Link></li>
                                    )}
                                    <li>
                                        <button onClick={auth.logout} className="ace-nav-button w-full justify-center">
                                            <UiLabel k="nav.title.logout" />
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
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
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
                        <Route path="/register" element={<Register />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/forgot-password" element={<ForgotPassword />} />
                        <Route path="/reset-password" element={<ResetPassword />} />
                        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
                        <Route path="/profile" element={<RequireAuth><UserProfile /></RequireAuth>} />
                        <Route path="/users" element={<RequireAuth><UserManagement /></RequireAuth>} />
                        <Route path="/admin/settings" element={<RequireAuth><AdminSettings /></RequireAuth>} />
                    </Routes>
                </Suspense>
            </main>
        </div>
    );
}

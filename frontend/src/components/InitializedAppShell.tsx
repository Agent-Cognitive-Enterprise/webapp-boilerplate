import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import RequireAuth from "./RequireAuth.tsx";
import { useKeepUserLoggedIn } from "../hooks/useKeepUserLoggedIn.ts";
import { useT } from "../hooks/useT.ts";
import { SETUP_SUPPORTED_LOCALES } from "../i18n/setupLocaleMeta.ts";
import { useInitializedAppShellState } from "./appShell/useInitializedAppShellState.ts";
import { AppShellNav } from "./appShell/AppShellNav.tsx";

const Register = lazy(() => import("./Register.tsx"));
const Login = lazy(() => import("./Login.tsx"));
const SetupWizard = lazy(() => import("./SetupWizard.tsx"));
const UserProfile = lazy(() => import("./UserProfile.tsx"));
const Dashboard = lazy(() => import("./Dashboard.tsx"));
const UserManagement = lazy(() => import("./UserManagement.tsx"));
const ForgotPassword = lazy(() => import("./ForgotPassword.tsx"));
const ResetPassword = lazy(() => import("./ResetPassword.tsx"));
const AdminSettings = lazy(() => import("./AdminSettings.tsx"));

export default function InitializedAppShell() {
    const siteLogoAltText = useT("app.alt.site_logo", undefined, "Site logo");
    const {
        auth,
        siteLogo,
        mobileNavOpen,
        setMobileNavOpen,
        backgroundUrl,
        isAdmin,
    } = useInitializedAppShellState();

    useKeepUserLoggedIn();

    return (
        <div
            data-testid="app-background-shell"
            className="relative min-h-screen w-full overflow-hidden bg-cover bg-center"
            style={backgroundUrl ? { backgroundImage: `url(${backgroundUrl})` } : undefined}
        >
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-slate-950/30 via-slate-900/15 to-slate-900/40" />
            <AppShellNav
                hasToken={Boolean(auth?.token)}
                isAdmin={isAdmin}
                mobileNavOpen={mobileNavOpen}
                onToggleMobileNav={() => setMobileNavOpen((prev) => !prev)}
                onLogout={auth?.logout ?? (() => undefined)}
                siteLogo={siteLogo}
                siteLogoAltText={siteLogoAltText}
            />

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

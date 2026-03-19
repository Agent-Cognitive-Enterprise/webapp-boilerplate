import { lazy, Suspense, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import InitializedAppShell from "./components/InitializedAppShell.tsx";
import { useBackendHealth } from "./hooks/useBackendHealth.ts";
import { useSetupBootstrap } from "./hooks/useSetupBootstrap.ts";

const SetupWizard = lazy(() => import("./components/SetupWizard.tsx"));
const POST_SETUP_REDIRECT_KEY = "postSetupRedirectToLogin";

function readPostSetupRedirectFlag(): boolean {
    if (typeof window === "undefined") {
        return false;
    }
    return window.sessionStorage.getItem(POST_SETUP_REDIRECT_KEY) === "true";
}

function writePostSetupRedirectFlag(): void {
    if (typeof window === "undefined") {
        return;
    }
    window.sessionStorage.setItem(POST_SETUP_REDIRECT_KEY, "true");
}

function clearPostSetupRedirectFlag(): void {
    if (typeof window === "undefined") {
        return;
    }
    window.sessionStorage.removeItem(POST_SETUP_REDIRECT_KEY);
}

function BackendOfflineOverlay({
    title,
    description,
}: {
    title: string;
    description: string;
}) {
    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm">
            <div className="w-full max-w-lg rounded-lg border border-gray-200 bg-white p-6 shadow-2xl">
                <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
                <p className="mt-2 text-gray-700">{description}</p>
            </div>
        </div>
    );
}

export default function App() {
    const navigate = useNavigate();
    const location = useLocation();
    const [shouldRedirectToLoginAfterSetup, setShouldRedirectToLoginAfterSetup] = useState(
        () => readPostSetupRedirectFlag(),
    );
    const {
        setupLoading,
        isInitialized,
        seedLocales,
        setupEmailDefaults,
        setupCopy,
        setIsInitialized,
    } = useSetupBootstrap();
    const { backendOffline } = useBackendHealth(false);

    const offlineOverlay = backendOffline ? (
        <BackendOfflineOverlay
            title={setupCopy.backendOfflineTitle}
            description={setupCopy.backendOfflineDescription}
        />
    ) : null;
    const shouldRedirectFromSetup = shouldRedirectToLoginAfterSetup || readPostSetupRedirectFlag();

    useEffect(() => {
        if (location.pathname === "/setup" || !shouldRedirectFromSetup) {
            return;
        }
        clearPostSetupRedirectFlag();
        setShouldRedirectToLoginAfterSetup(false);
    }, [location.pathname, shouldRedirectFromSetup]);

    useEffect(() => {
        if (!isInitialized || location.pathname !== "/setup" || !shouldRedirectFromSetup) {
            return;
        }
        navigate("/login", { replace: true });
    }, [isInitialized, location.pathname, navigate, shouldRedirectFromSetup]);

    if (setupLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-gray-50 text-gray-700">
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
                                    onSetupComplete={() => {
                                        writePostSetupRedirectFlag();
                                        setShouldRedirectToLoginAfterSetup(true);
                                        setIsInitialized(true);
                                    }}
                                    seedLocales={seedLocales}
                                    emailDefaults={setupEmailDefaults}
                                />
                            }
                        />
                        <Route path="*" element={<Navigate to="/setup" replace />} />
                    </Routes>
                </Suspense>
                {offlineOverlay}
            </div>
        );
    }

    if (isInitialized && location.pathname === "/setup") {
        if (shouldRedirectFromSetup) {
            return <div className="min-h-[40vh]" />;
        }
        return (
            <Suspense fallback={<div className="min-h-[40vh]" />}>
                <SetupWizard isInitialized={true} onSetupComplete={() => undefined} seedLocales={seedLocales} />
            </Suspense>
        );
    }

    return (
        <div className="relative min-h-screen">
            <InitializedAppShell />
            {offlineOverlay}
        </div>
    );
}

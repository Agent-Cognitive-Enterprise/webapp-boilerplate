import { useEffect, useState } from "react";

const DEFAULT_HEALTH_CHECK_INTERVAL_MS = 10000;
const HEALTH_CHECK_TIMEOUT_MS = 5000;

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

function getHealthCheckInterval(): number {
    const rawValue = import.meta.env.VITE_BACKEND_POLL_INTERVAL;
    const parsed = Number(rawValue);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_HEALTH_CHECK_INTERVAL_MS;
}

export function useBackendHealth(initialOffline = false) {
    const [backendOffline, setBackendOffline] = useState(initialOffline);

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
        }, getHealthCheckInterval());

        return () => {
            active = false;
            window.clearInterval(intervalId);
        };
    }, []);

    return { backendOffline, setBackendOffline };
}

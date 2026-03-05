// /frontend/src/api/api.ts

import axios from "axios";
import type {AxiosError, AxiosResponse} from "axios";
import {AxiosHeaders} from "axios";
import type {ExtendedAxiosRequestConfig, RefreshResponse} from "./types";

// Clear the one-shot reload flag if present (prevents reload loops)
if (typeof window !== "undefined") {
    try {
        if (sessionStorage.getItem("reloadedAfterBackendRestore") === "1") {
            sessionStorage.removeItem("reloadedAfterBackendRestore");
        }
    } catch {
        // ignore unavailability of sessionStorage
    }
}

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
    withCredentials: true,
});

let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

let successSubs: Array<(token: string) => void> = [];
let errorSubs: Array<(err: unknown) => void> = [];

// Track backend connectivity state
let backendDown = false;

function subscribeTokenRefresh(onSuccess: (token: string) => void, onError: (err: unknown) => void) {
    successSubs.push(onSuccess);
    errorSubs.push(onError);
}

function notifySubscribersSuccess(token: string) {
    successSubs.forEach(cb => {
        try {
            cb(token);
        } catch {
            // Intentionally empty
        }
    });
    successSubs = [];
    errorSubs = [];
}

function notifySubscribersError(err: unknown) {
    errorSubs.forEach(cb => {
        try {
            cb(err);
        } catch {
            // Intentionally empty
        }
    });
    successSubs = [];
    errorSubs = [];
}

// ----------------------
// Request interceptor
// ----------------------
api.interceptors.request.use((config) => {
    const cfg = config as ExtendedAxiosRequestConfig;
    if (!cfg.headers) cfg.headers = new AxiosHeaders();
    if (!cfg.skipAuthHeader) {
        const token = localStorage.getItem("token");
        if (token) (cfg.headers as Record<string, string>).Authorization = `Bearer ${token}`;
    }
    return cfg;
});

// ----------------------
// Response interceptor: auto-refresh and backend restore detection
// ----------------------
api.interceptors.response.use(
    (res: AxiosResponse) => {
        // If backend was down and we just received a successful response, reload once
        if (backendDown) {
            backendDown = false;
            try {
                sessionStorage.setItem("reloadedAfterBackendRestore", "1");
            } catch {
                // ignore
            }
            // Full reload to reinitialize app state after outage
            if (typeof window !== "undefined") {
                window.location.reload();
            }
        }
        return res;
    },
    async (err: AxiosError) => {
        const original = err.config as ExtendedAxiosRequestConfig | undefined;
        // Ignore client-side cancellations; they are not backend outages.
        // Locale switches can cancel in-flight label requests during rerenders.
        if (err.code === "ERR_CANCELED" || axios.isCancel(err)) {
            return Promise.reject(err);
        }
        // Detect backend outage/network errors (no response or gateway/service unavailable/timeouts)
        const status = err.response?.status;
        const maybeDown = !err.response || status === 502 || status === 503 || status === 504;
        if (maybeDown) {
            backendDown = true;
        }

        if (!original || original.skipAuthRefresh) return Promise.reject(err);

        if (status === 401 && !original._retry) {
            original._retry = true;

            // Queue if refresh in progress
            if (isRefreshing && refreshPromise) {
                return new Promise((resolve, reject) => {
                    subscribeTokenRefresh(
                        newToken => {
                            const retryConfig: ExtendedAxiosRequestConfig = {
                                ...original,
                                _retry: true,
                                headers: new AxiosHeaders({...(original.headers || {}), Authorization: `Bearer ${newToken}`}),
                            };
                            resolve(api.request(retryConfig));
                        },
                        err => reject(err)
                    );
                });
            }

            // Start refresh
            isRefreshing = true;
            refreshPromise = (async () => {
                const resp = await api.post("/auth/refresh", undefined, {
                    skipAuthHeader: true,
                    skipAuthRefresh: true,
                } as ExtendedAxiosRequestConfig);
                const newToken = (resp.data as RefreshResponse)?.access_token;
                if (typeof newToken !== "string") throw new Error("Invalid refresh token");
                localStorage.setItem("token", newToken);
                notifySubscribersSuccess(newToken);
                return newToken;
            })();

            try {
                const newToken = await refreshPromise;
                const retryConfig: ExtendedAxiosRequestConfig = {
                    ...original,
                    _retry: true,
                    headers: new AxiosHeaders({...(original.headers || {}), Authorization: `Bearer ${newToken}`}),
                };
                return api.request(retryConfig);
            } catch (refreshErr) {
                notifySubscribersError(refreshErr);
                localStorage.removeItem("token");
                window.location.href = "/login";
                return Promise.reject(refreshErr);
            } finally {
                isRefreshing = false;
                refreshPromise = null;
            }
        }

        return Promise.reject(err);
    }
);

export default api;

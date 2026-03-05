// /frontend/src/contexts/UiLabelProvider.tsx

import React, {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
} from "react";
import api from "../api/api";
import {AuthContext} from "./AuthContext";

// Helper to build composite key
function k2(key: string, locale: string) {
    return `${key}::${locale}`;
}

export type UILabelListener = (value: string | undefined) => void;
export type UiLabelContextType = {
    getValue: (key: string, locale: string) => string | undefined;
    subscribe: (key: string, locale: string, cb: UILabelListener) => () => void;
    request: (key: string, locale: string) => Promise<void>;
    suggest: (key: string, locale: string, value: string) => Promise<void>;
};

// LocalStorage key
const LS_KEY = "ui_label_cache_v1";
// Freshness threshold (1 hour)
const FRESHNESS_MS = 60 * 60 * 1000;
// Polling params for "add" / "suggest" wait loops
const POLL_INTERVAL_MS = 60 * 1000;
const POLL_MAX_ATTEMPTS = 10;

// LocalStorage shape per locale:
// {
//   [locale]: {
//     values: { [key: string]: string },
//     values_hash: string,
//     last_check: number (ms since epoch)
//   }
// }

function loadLocalCache(): Record<string, any> {
    try {
        const raw = localStorage.getItem(LS_KEY);

        if (!raw) return {};

        return JSON.parse(raw);
    } catch {
        return {};
    }
}


function saveLocalCache(obj: Record<string, any>) {
    try {
        localStorage.setItem(LS_KEY, JSON.stringify(obj));
    } catch {
        // ignore
    }
}

const UiLabelCtx = createContext<UiLabelContextType | undefined>(undefined);

export const UiLabelProvider: React.FC<{ children: React.ReactNode }> = ({
                                                                             children,
                                                                         }) => {
    const auth = useContext(AuthContext);
    if (!auth) throw new Error("AuthContext not available");
    const {token} = auth;

    // In-memory cache map for quick reads (key::locale -> value)
    const cacheRef = useRef<Map<string, string>>(new Map());

    // LocalStorage-backed per-locale cache
    const localCacheRef = useRef<Record<string, any>>(loadLocalCache());

    // subsRef: locale -> key -> Set<listeners>
    const subsRef = useRef<Map<string, Map<string, Set<UILabelListener>>>>(
        new Map()
    );

    // Per-locale in-progress fetch lock (to avoid duplicate GETs)
    const fetchingLocaleRef = useRef<Map<string, boolean>>(new Map());

    // Notify listeners for a key+locale
    const notify = useCallback((key: string, locale: string) => {
        const listeners = subsRef.current.get(locale)?.get(key);
        const value = cacheRef.current.get(k2(key, locale));
        if (listeners) {
            listeners.forEach((cb) => {
                // console.log("notifying:", key, locale, value);
                try {
                    cb(value);
                } catch {
                    // ignore individual listener errors
                }
            });
        }
    }, []);

    // Load a given locale into the memory cache from localCacheRef
    const loadLocaleIntoMemory = useCallback((locale: string) => {
        const entry = localCacheRef.current[locale];

        if (!entry || !entry.values) return;

        for (const [k, v] of Object.entries(entry.values)) {
            cacheRef.current.set(k2(k, locale), v as string);
        }
    }, []);

    // Replace the entire locale cache (called when BE returns new labels)
    const setLocaleCache = useCallback(
        (locale: string, labels: Record<string, string>, values_hash?: string) => {
            if (!localCacheRef.current) localCacheRef.current = {};
            localCacheRef.current[locale] = {
                values: labels,
                values_hash: values_hash ?? localCacheRef.current[locale]?.values_hash,
                last_check: Date.now(),
            };
            saveLocalCache(localCacheRef.current);

            // Update in-memory cache and notify
            for (const [key, value] of Object.entries(labels)) {
                cacheRef.current.set(k2(key, locale), value);
                notify(key, locale);
            }
        },
        [notify]
    );

    // Update last_check only
    const touchLocaleLastCheck = useCallback((locale: string) => {
        if (!localCacheRef.current) localCacheRef.current = {};
        if (!localCacheRef.current[locale]) {
            localCacheRef.current[locale] = {values: {}, values_hash: undefined, last_check: Date.now()};
        } else {
            localCacheRef.current[locale].last_check = Date.now();
        }
        saveLocalCache(localCacheRef.current);
    }, []);

    // Helper: get value from memory/local cache
    const getValue = useCallback((key: string, locale: string) => {
        // try memory cache first
        const mem = cacheRef.current.get(k2(key, locale));
        if (mem !== undefined) return mem;
        // fallback to localCacheRef
        const entry = localCacheRef.current[locale];
        if (entry && entry.values && entry.values[key] !== undefined) {
            const v = entry.values[key];
            // seed mem cache
            cacheRef.current.set(k2(key, locale), v);
            return v;
        }
        return undefined;
    }, []);

    // Network: Fetch locale "get" with free bearer if stale or missing
    const fetchLocaleIfStale = useCallback(
        async (locale: string) => {
            // prevent concurrent fetches for same locale
            if (fetchingLocaleRef.current.get(locale)) return;

            fetchingLocaleRef.current.set(locale, true);

            try {
                // Determine if we need to fetch
                const entry = localCacheRef.current[locale];
                const values_hash = entry?.values_hash;

                try {
                    const resp = await api.post(
                        "/ui-label",
                        {
                            action: "get",
                            locale,
                            values_hash,
                        },
                        {
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: `Bearer free`,
                            },
                        }
                    );

                    const payload = resp?.data;
                    if (!payload) return;

                    // console.log("fetchLocaleIfStale payload:", payload);

                    // If BE returns the same values_hash - only touch last_check
                    if (payload?.data?.values_hash === values_hash) {
                        // update last_check, keep values the same
                        touchLocaleLastCheck(locale);

                        return;
                    }

                    // Otherwise expect payload.data.labels and payload.data.values_hash
                    // (older code returned data:{labels,...})
                    const data = payload?.data ?? payload;

                    // console.log("fetchLocaleIfStale data:", data);

                    if (data
                        && data.labels
                        && typeof data.labels === "object") {

                        const labels: Record<string, string> = data.labels;
                        const newHash = data.values_hash ?? data.valuesHash ?? localCacheRef.current[locale]?.values_hash;
                        setLocaleCache(locale, labels, newHash);

                        return;
                    }

                    // Fallback: if payload.data is an array of UILabelItem[] (rare)
                    if (Array.isArray(data)) {

                        const labels: Record<string, string> = {};
                        for (const it of data) {
                            labels[it.key] = it.value;
                        }
                        // compute newHash unknown here; leave existing
                        setLocaleCache(locale, labels, localCacheRef.current[locale]?.values_hash);

                        return;
                    }

                    // If the payload has values_hash only (no labels) and not "no changes" - only touch
                    if (data
                        && data.values_hash) {

                        touchLocaleLastCheck(locale);

                        return;
                    }
                } catch {
                    // network error - swallow; we'll try next time
                }
            } finally {
                fetchingLocaleRef.current.set(locale, false);
            }
        },
        [setLocaleCache, touchLocaleLastCheck]
    );

    // When a key is missing for a given locale, call "add" and start polling loop
    const ensureKeyExists = useCallback(
        async (key: string, locale: string) => {
            // If we already have it now, nothing to do
            if (getValue(key, locale) !== undefined) return;

            // Send add request using free bearer
            try {
                await api.post(
                    "/ui-label",
                    {
                        action: "add",
                        locale,
                        key,
                    },
                    {
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer free`,
                        },
                        // skipAuthRefresh: true,
                    }
                );
            } catch {
                // ignore - we'll poll anyway
            }

            // Now poll every minute up to POLL_MAX_ATTEMPTS times
            for (let attempt = 0; attempt < POLL_MAX_ATTEMPTS; attempt++) {
                await new Promise((res) => setTimeout(res, POLL_INTERVAL_MS));
                // fetch the whole locale if stale (this will update the local cache if translations appear)
                await fetchLocaleIfStale(locale);
                // If the key is present now, notify and exit
                const v = getValue(key, locale);
                if (v !== undefined) {
                    // we got actual locale translation
                    notify(key, locale);
                    return;
                }
            }
            // After polling exhausted - leave locale as missing.
            // UI fallback should come from the dedicated English subscription in UiLabel.
        },
        [fetchLocaleIfStale, getValue, notify]
    );

    // When a suggestion is posted (authenticated), poll similarly to detect acceptance/updated translation
    const pollAfterSuggest = useCallback(
        async (key: string, locale: string) => {
            for (let attempt = 0; attempt < POLL_MAX_ATTEMPTS; attempt++) {
                await new Promise((res) => setTimeout(res, POLL_INTERVAL_MS));
                await fetchLocaleIfStale(locale);
                const v = getValue(key, locale);
                if (v !== undefined) {
                    notify(key, locale);
                    return;
                }
            }
        },
        [fetchLocaleIfStale, getValue, notify]
    );

    // request exposed to components: ensure locale freshness (hourly) - triggers GET if needed
    const request = useCallback(
        async (key: string, locale: string) => {
            // Seed local memory from localCache if available
            loadLocaleIntoMemory(locale);

            // If we already have translation for a key, still ensure locale freshness when needed
            const entry = localCacheRef.current[locale];
            const now = Date.now();

            // Determine if we need to fetch:
            // 1. missing locale
            // 2. missing last_check
            // 3. stale last_check
            // 4. empty values object
            const needsFetch =
                !entry ||
                !entry.last_check ||
                now - entry.last_check > FRESHNESS_MS ||
                !entry.values ||
                Object.keys(entry.values).length === 0;

            // console.log("request:", key, locale, needsFetch);

            if (needsFetch) {
                // console.log("fetching locale:", locale);
                await fetchLocaleIfStale(locale);
            }

            // If still missing the key after fetch, start an add/poll process (but do not block)
            if (getValue(key, locale) === undefined) {
                // fire-and-forget
                ensureKeyExists(key, locale).catch(() => {
                    /* ignore */
                });
            }
        },
        [ensureKeyExists, fetchLocaleIfStale, getValue, loadLocaleIntoMemory]
    );

    // Suggest a new value (authenticated)
    const suggest = useCallback(
        async (key: string, locale: string, value: string) => {
            // Must have an authenticated token
            if (!token) {
                throw new Error("Unauthorized");
            }

            await api.post(
                "/ui-label",
                {
                    action: "suggest",
                    key,
                    locale,
                    value,
                },
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            // Start polling to detect suggestion being accepted/updated on BE.
            // Use free bearer GET in fetchLocaleIfStale to detect changes.
            // Fire-and-forget
            pollAfterSuggest(key, locale).catch(() => {
                /* ignore */
            });
        },
        [token, pollAfterSuggest]
    );

    // subscribe: register listener; return unsubscribe
    const subscribe = useCallback(
        (key: string, locale: string, cb: UILabelListener) => {

            if (!subsRef.current.has(locale)) subsRef.current.set(locale, new Map());

            const byKey = subsRef.current.get(locale)!;

            if (!byKey.has(key)) byKey.set(key, new Set());

            byKey.get(key)!.add(cb);

            // Ensure we have seed value in memory (from localStorage) so listener can get current value
            loadLocaleIntoMemory(locale);

            // Immediately call listener with the current value (could be undefined)
            try {
                cb(getValue(key, locale));
            } catch {
                // ignore
            }

            // If missing, trigger the add/poll workflow
            if (getValue(key, locale) === undefined) {
                // do not await
                ensureKeyExists(key, locale).catch(() => {
                    /* ignore */
                });
            } else {
                // ensure freshness for locale
                request(key, locale).catch(() => {
                    /* ignore */
                });
            }

            return () => {
                const listeners = subsRef.current.get(locale)?.get(key);
                if (listeners) {

                    listeners.delete(cb);

                    if (listeners.size === 0) subsRef.current.get(locale)!.delete(key);
                }
            };
        },
        [ensureKeyExists, getValue, loadLocaleIntoMemory, request]
    );

    // On mount, load all localCache into memory (fast reads)
    useEffect(() => {

        const all = localCacheRef.current;

        for (const locale of Object.keys(all)) {
            loadLocaleIntoMemory(locale);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Expose context
    const ctxValue = useMemo<UiLabelContextType>(
        () => ({
            getValue,
            subscribe,
            request,
            suggest,
        }),
        [getValue, subscribe, request, suggest]
    );

    return <UiLabelCtx.Provider value={ctxValue}>{children}</UiLabelCtx.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export function useUiLabelContext(): UiLabelContextType {
    const ctx = useContext(UiLabelCtx);
    if (!ctx) throw new Error("UILabel provider is missing");
    return ctx;
}

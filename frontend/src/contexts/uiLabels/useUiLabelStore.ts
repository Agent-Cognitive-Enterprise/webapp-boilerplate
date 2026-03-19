import {useCallback, useEffect, useMemo, useRef} from "react";
import api from "../../api/api";
import {
    loadUiLabelLocaleIntoMemory,
    loadUiLabelLocalCache,
    readUiLabelValue,
    replaceUiLabelLocaleCache,
    touchUiLabelLocaleLastCheck,
    UI_LABEL_FRESHNESS_MS,
    UI_LABEL_POLL_INTERVAL_MS,
    UI_LABEL_POLL_MAX_ATTEMPTS,
} from "./cache";
import type {UILabelListener, UiLabelContextType, UiLabelLocalCache} from "./types";

type UiLabelPayload = {
    data?: {
        labels?: Record<string, string>;
        values_hash?: string;
        valuesHash?: string;
    };
    labels?: Record<string, string>;
    values_hash?: string;
};

type UiLabelArrayItem = {
    key: string;
    value: string;
};

type UiLabelHashPayload = {
    values_hash?: string;
    valuesHash?: string;
};

export function useUiLabelStore(token: string | null | undefined): UiLabelContextType {
    const cacheRef = useRef<Map<string, string>>(new Map());
    const localCacheRef = useRef<UiLabelLocalCache>(loadUiLabelLocalCache());
    const subsRef = useRef<Map<string, Map<string, Set<UILabelListener>>>>(new Map());
    const fetchingLocaleRef = useRef<Map<string, boolean>>(new Map());

    const notify = useCallback((key: string, locale: string) => {
        const listeners = subsRef.current.get(locale)?.get(key);
        const value = cacheRef.current.get(`${key}::${locale}`);

        listeners?.forEach((cb) => {
            try {
                cb(value);
            } catch {
                // ignore listener errors
            }
        });
    }, []);

    const loadLocaleIntoMemory = useCallback((locale: string) => {
        loadUiLabelLocaleIntoMemory(cacheRef.current, localCacheRef.current, locale);
    }, []);

    const getValue = useCallback((key: string, locale: string) => {
        return readUiLabelValue(cacheRef.current, localCacheRef.current, key, locale);
    }, []);

    const setLocaleCache = useCallback(
        (locale: string, labels: Record<string, string>, valuesHash?: string) => {
            replaceUiLabelLocaleCache(
                cacheRef.current,
                localCacheRef.current,
                locale,
                labels,
                notify,
                valuesHash,
            );
        },
        [notify],
    );

    const touchLocaleLastCheck = useCallback((locale: string) => {
        touchUiLabelLocaleLastCheck(localCacheRef.current, locale);
    }, []);

    const fetchLocaleIfStale = useCallback(
        async (locale: string) => {
            if (fetchingLocaleRef.current.get(locale)) {
                return;
            }

            fetchingLocaleRef.current.set(locale, true);

            try {
                const entry = localCacheRef.current[locale];
                const valuesHash = entry?.values_hash;

                try {
                    const resp = await api.post(
                        "/ui-label",
                        {
                            action: "get",
                            locale,
                            values_hash: valuesHash,
                        },
                        {
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: "Bearer free",
                            },
                        },
                    );

                    const payload = resp?.data as UiLabelPayload | UiLabelArrayItem[] | undefined;

                    if (!payload) {
                        return;
                    }

                    if (!Array.isArray(payload) && payload.data?.values_hash === valuesHash) {
                        touchLocaleLastCheck(locale);
                        return;
                    }

                    const data = !Array.isArray(payload) ? payload.data ?? payload : payload;

                    if (
                        !Array.isArray(data) &&
                        data.labels &&
                        typeof data.labels === "object"
                    ) {
                        const hashPayload = data as UiLabelHashPayload;
                        setLocaleCache(
                            locale,
                            data.labels,
                            hashPayload.values_hash ??
                                hashPayload.valuesHash ??
                                localCacheRef.current[locale]?.values_hash,
                        );
                        return;
                    }

                    if (Array.isArray(data)) {
                        const labels = data.reduce<Record<string, string>>((acc, item) => {
                            acc[item.key] = item.value;
                            return acc;
                        }, {});
                        setLocaleCache(locale, labels, localCacheRef.current[locale]?.values_hash);
                        return;
                    }

                    if (!Array.isArray(data) && data.values_hash) {
                        touchLocaleLastCheck(locale);
                    }
                } catch {
                    // ignore network errors and retry on next request
                }
            } finally {
                fetchingLocaleRef.current.set(locale, false);
            }
        },
        [setLocaleCache, touchLocaleLastCheck],
    );

    const ensureKeyExists = useCallback(
        async (key: string, locale: string) => {
            if (getValue(key, locale) !== undefined) {
                return;
            }

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
                            Authorization: "Bearer free",
                        },
                    },
                );
            } catch {
                // ignore add failures and rely on polling
            }

            for (let attempt = 0; attempt < UI_LABEL_POLL_MAX_ATTEMPTS; attempt++) {
                await new Promise((resolve) => setTimeout(resolve, UI_LABEL_POLL_INTERVAL_MS));
                await fetchLocaleIfStale(locale);

                if (getValue(key, locale) !== undefined) {
                    notify(key, locale);
                    return;
                }
            }
        },
        [fetchLocaleIfStale, getValue, notify],
    );

    const pollAfterSuggest = useCallback(
        async (key: string, locale: string) => {
            for (let attempt = 0; attempt < UI_LABEL_POLL_MAX_ATTEMPTS; attempt++) {
                await new Promise((resolve) => setTimeout(resolve, UI_LABEL_POLL_INTERVAL_MS));
                await fetchLocaleIfStale(locale);

                if (getValue(key, locale) !== undefined) {
                    notify(key, locale);
                    return;
                }
            }
        },
        [fetchLocaleIfStale, getValue, notify],
    );

    const request = useCallback(
        async (key: string, locale: string) => {
            loadLocaleIntoMemory(locale);

            const entry = localCacheRef.current[locale];
            const now = Date.now();
            const needsFetch =
                !entry ||
                !entry.last_check ||
                now - entry.last_check > UI_LABEL_FRESHNESS_MS ||
                !entry.values ||
                Object.keys(entry.values).length === 0;

            if (needsFetch) {
                await fetchLocaleIfStale(locale);
            }

            if (getValue(key, locale) === undefined) {
                ensureKeyExists(key, locale).catch(() => {
                    // ignore background add/poll failures
                });
            }
        },
        [ensureKeyExists, fetchLocaleIfStale, getValue, loadLocaleIntoMemory],
    );

    const suggest = useCallback(
        async (key: string, locale: string, value: string) => {
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
                },
            );

            pollAfterSuggest(key, locale).catch(() => {
                // ignore background polling failures
            });
        },
        [pollAfterSuggest, token],
    );

    const subscribe = useCallback(
        (key: string, locale: string, cb: UILabelListener) => {
            if (!subsRef.current.has(locale)) {
                subsRef.current.set(locale, new Map());
            }

            const byKey = subsRef.current.get(locale)!;

            if (!byKey.has(key)) {
                byKey.set(key, new Set());
            }

            byKey.get(key)!.add(cb);
            loadLocaleIntoMemory(locale);

            try {
                cb(getValue(key, locale));
            } catch {
                // ignore listener errors
            }

            if (getValue(key, locale) === undefined) {
                ensureKeyExists(key, locale).catch(() => {
                    // ignore background add/poll failures
                });
            } else {
                request(key, locale).catch(() => {
                    // ignore background refresh failures
                });
            }

            return () => {
                const listeners = subsRef.current.get(locale)?.get(key);

                if (!listeners) {
                    return;
                }

                listeners.delete(cb);

                if (listeners.size === 0) {
                    subsRef.current.get(locale)?.delete(key);
                }
            };
        },
        [ensureKeyExists, getValue, loadLocaleIntoMemory, request],
    );

    useEffect(() => {
        for (const locale of Object.keys(localCacheRef.current)) {
            loadLocaleIntoMemory(locale);
        }
    }, [loadLocaleIntoMemory]);

    return useMemo(
        () => ({
            getValue,
            subscribe,
            request,
            suggest,
        }),
        [getValue, request, subscribe, suggest],
    );
}

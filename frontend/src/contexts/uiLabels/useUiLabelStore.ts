import {useCallback, useEffect, useMemo, useRef} from "react";
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
import {pollUntilUiLabelAvailable} from "./polling";
import {notifyUiLabelListeners, subscribeUiLabelListener} from "./subscriptions";
import {addUiLabelKey, fetchUiLabelLocale, suggestUiLabelValue} from "./uiLabelApi";
import type {UILabelListener, UiLabelContextType, UiLabelLocalCache} from "./types";

export function useUiLabelStore(token: string | null | undefined): UiLabelContextType {
    const cacheRef = useRef<Map<string, string>>(new Map());
    const localCacheRef = useRef<UiLabelLocalCache>(loadUiLabelLocalCache());
    const subsRef = useRef<Map<string, Map<string, Set<UILabelListener>>>>(new Map());
    const fetchingLocaleRef = useRef<Map<string, boolean>>(new Map());

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
                (key, targetLocale) => {
                    notifyUiLabelListeners(subsRef.current, getValue, key, targetLocale);
                },
                valuesHash,
            );
        },
        [getValue],
    );

    const touchLocaleLastCheck = useCallback((locale: string) => {
        touchUiLabelLocaleLastCheck(localCacheRef.current, locale);
    }, []);

    const notify = useCallback(
        (key: string, locale: string) => {
            notifyUiLabelListeners(subsRef.current, getValue, key, locale);
        },
        [getValue],
    );

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
                    const result = await fetchUiLabelLocale(locale, valuesHash);

                    if (!result) {
                        return;
                    }

                    if (result.kind === "unchanged" || result.kind === "touched") {
                        touchLocaleLastCheck(locale);
                        return;
                    }

                    setLocaleCache(locale, result.labels, result.valuesHash);
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
                await addUiLabelKey(locale, key);
            } catch {
                // ignore add failures and rely on polling
            }

            await pollUntilUiLabelAvailable({
                key,
                locale,
                maxAttempts: UI_LABEL_POLL_MAX_ATTEMPTS,
                intervalMs: UI_LABEL_POLL_INTERVAL_MS,
                fetchLocaleIfStale,
                getValue,
                notify,
            });
        },
        [fetchLocaleIfStale, getValue, notify],
    );

    const pollAfterSuggest = useCallback(
        async (key: string, locale: string) => {
            await pollUntilUiLabelAvailable({
                key,
                locale,
                maxAttempts: UI_LABEL_POLL_MAX_ATTEMPTS,
                intervalMs: UI_LABEL_POLL_INTERVAL_MS,
                fetchLocaleIfStale,
                getValue,
                notify,
            });
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
            await suggestUiLabelValue(token, key, locale, value);

            pollAfterSuggest(key, locale).catch(() => {
                // ignore background polling failures
            });
        },
        [pollAfterSuggest, token],
    );

    const subscribe = useCallback(
        (key: string, locale: string, cb: UILabelListener) => {
            const unsubscribe = subscribeUiLabelListener(subsRef.current, key, locale, cb);
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

            return unsubscribe;
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

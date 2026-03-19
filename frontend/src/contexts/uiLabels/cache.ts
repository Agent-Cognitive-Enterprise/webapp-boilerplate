import type {UiLabelLocalCache} from "./types";

export const UI_LABEL_LOCAL_STORAGE_KEY = "ui_label_cache_v1";
export const UI_LABEL_FRESHNESS_MS = 60 * 60 * 1000;
export const UI_LABEL_POLL_INTERVAL_MS = 60 * 1000;
export const UI_LABEL_POLL_MAX_ATTEMPTS = 10;

export function buildUiLabelCacheKey(key: string, locale: string): string {
    return `${key}::${locale}`;
}

export function loadUiLabelLocalCache(): UiLabelLocalCache {
    try {
        const raw = localStorage.getItem(UI_LABEL_LOCAL_STORAGE_KEY);

        if (!raw) {
            return {};
        }

        return JSON.parse(raw) as UiLabelLocalCache;
    } catch {
        return {};
    }
}

export function saveUiLabelLocalCache(localCache: UiLabelLocalCache): void {
    try {
        localStorage.setItem(UI_LABEL_LOCAL_STORAGE_KEY, JSON.stringify(localCache));
    } catch {
        // ignore localStorage errors
    }
}

export function loadUiLabelLocaleIntoMemory(
    memoryCache: Map<string, string>,
    localCache: UiLabelLocalCache,
    locale: string,
): void {
    const entry = localCache[locale];

    if (!entry?.values) {
        return;
    }

    for (const [key, value] of Object.entries(entry.values)) {
        memoryCache.set(buildUiLabelCacheKey(key, locale), value);
    }
}

export function readUiLabelValue(
    memoryCache: Map<string, string>,
    localCache: UiLabelLocalCache,
    key: string,
    locale: string,
): string | undefined {
    const memoryValue = memoryCache.get(buildUiLabelCacheKey(key, locale));

    if (memoryValue !== undefined) {
        return memoryValue;
    }

    const cachedValue = localCache[locale]?.values?.[key];

    if (cachedValue !== undefined) {
        memoryCache.set(buildUiLabelCacheKey(key, locale), cachedValue);
    }

    return cachedValue;
}

export function replaceUiLabelLocaleCache(
    memoryCache: Map<string, string>,
    localCache: UiLabelLocalCache,
    locale: string,
    labels: Record<string, string>,
    notify: (key: string, locale: string) => void,
    valuesHash?: string,
): void {
    localCache[locale] = {
        values: labels,
        values_hash: valuesHash ?? localCache[locale]?.values_hash,
        last_check: Date.now(),
    };
    saveUiLabelLocalCache(localCache);

    for (const [key, value] of Object.entries(labels)) {
        memoryCache.set(buildUiLabelCacheKey(key, locale), value);
        notify(key, locale);
    }
}

export function touchUiLabelLocaleLastCheck(
    localCache: UiLabelLocalCache,
    locale: string,
): void {
    localCache[locale] = {
        values: localCache[locale]?.values ?? {},
        values_hash: localCache[locale]?.values_hash,
        last_check: Date.now(),
    };
    saveUiLabelLocalCache(localCache);
}

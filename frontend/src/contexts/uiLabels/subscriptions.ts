import type {UILabelListener} from "./types";

export type UiLabelSubscriptions = Map<string, Map<string, Set<UILabelListener>>>;

export function notifyUiLabelListeners(
    subscriptions: UiLabelSubscriptions,
    getValue: (key: string, locale: string) => string | undefined,
    key: string,
    locale: string,
): void {
    const listeners = subscriptions.get(locale)?.get(key);
    const value = getValue(key, locale);

    listeners?.forEach((cb) => {
        try {
            cb(value);
        } catch {
            // ignore listener errors
        }
    });
}

export function subscribeUiLabelListener(
    subscriptions: UiLabelSubscriptions,
    key: string,
    locale: string,
    listener: UILabelListener,
): () => void {
    if (!subscriptions.has(locale)) {
        subscriptions.set(locale, new Map());
    }

    const byKey = subscriptions.get(locale)!;

    if (!byKey.has(key)) {
        byKey.set(key, new Set());
    }

    byKey.get(key)!.add(listener);

    return () => {
        const listeners = subscriptions.get(locale)?.get(key);

        if (!listeners) {
            return;
        }

        listeners.delete(listener);

        if (listeners.size === 0) {
            subscriptions.get(locale)?.delete(key);
        }

        if (subscriptions.get(locale)?.size === 0) {
            subscriptions.delete(locale);
        }
    };
}

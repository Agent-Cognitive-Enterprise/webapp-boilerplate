export async function pollUntilUiLabelAvailable(params: {
    key: string;
    locale: string;
    maxAttempts: number;
    intervalMs: number;
    fetchLocaleIfStale: (locale: string) => Promise<void>;
    getValue: (key: string, locale: string) => string | undefined;
    notify: (key: string, locale: string) => void;
    wait?: (ms: number) => Promise<void>;
}): Promise<boolean> {
    const {
        key,
        locale,
        maxAttempts,
        intervalMs,
        fetchLocaleIfStale,
        getValue,
        notify,
        wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms)),
    } = params;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await wait(intervalMs);
        await fetchLocaleIfStale(locale);

        if (getValue(key, locale) !== undefined) {
            notify(key, locale);
            return true;
        }
    }

    return false;
}

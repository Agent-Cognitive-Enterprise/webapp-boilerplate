export type UILabelListener = (value: string | undefined) => void;

export type UiLabelContextType = {
    getValue: (key: string, locale: string) => string | undefined;
    subscribe: (key: string, locale: string, cb: UILabelListener) => () => void;
    request: (key: string, locale: string) => Promise<void>;
    suggest: (key: string, locale: string, value: string) => Promise<void>;
};

export type UiLabelLocaleCacheEntry = {
    values: Record<string, string>;
    values_hash?: string;
    last_check?: number;
};

export type UiLabelLocalCache = Record<string, UiLabelLocaleCacheEntry | undefined>;

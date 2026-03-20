import api from "../../api/api";

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

export type FetchUiLabelLocaleResult =
    | {
        kind: "unchanged";
    }
    | {
        kind: "labels";
        labels: Record<string, string>;
        valuesHash?: string;
    }
    | {
        kind: "touched";
    };

export function normalizeUiLabelFetchPayload(
    payload: UiLabelPayload | UiLabelArrayItem[] | undefined,
    currentValuesHash?: string,
): FetchUiLabelLocaleResult | null {
    if (!payload) {
        return null;
    }

    if (!Array.isArray(payload) && payload.data?.values_hash === currentValuesHash) {
        return {kind: "unchanged"};
    }

    const data = Array.isArray(payload) ? payload : payload.data ?? payload;

    if (!Array.isArray(data) && data.labels && typeof data.labels === "object") {
        const hashPayload = data as UiLabelHashPayload;
        return {
            kind: "labels",
            labels: data.labels,
            valuesHash: hashPayload.values_hash ?? hashPayload.valuesHash ?? currentValuesHash,
        };
    }

    if (Array.isArray(data)) {
        return {
            kind: "labels",
            labels: data.reduce<Record<string, string>>((acc, item) => {
                acc[item.key] = item.value;
                return acc;
            }, {}),
            valuesHash: currentValuesHash,
        };
    }

    if (!Array.isArray(data) && data.values_hash) {
        return {kind: "touched"};
    }

    return null;
}

export async function fetchUiLabelLocale(
    locale: string,
    valuesHash?: string,
): Promise<FetchUiLabelLocaleResult | null> {
    const response = await api.post(
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

    return normalizeUiLabelFetchPayload(
        response?.data as UiLabelPayload | UiLabelArrayItem[] | undefined,
        valuesHash,
    );
}

export async function addUiLabelKey(locale: string, key: string): Promise<void> {
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
}

export async function suggestUiLabelValue(
    token: string | null | undefined,
    key: string,
    locale: string,
    value: string,
): Promise<void> {
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
}

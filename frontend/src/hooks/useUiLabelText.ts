import {useMemo} from "react";
import {useUiLabel} from "./useUiLabel";
import { getPreferredUiLocale } from "../i18n/uiLocale.ts";

export function resolveUiLabelLocale(localeOverride?: string): string {
    return getPreferredUiLocale(localeOverride);
}

export function applyUiLabelFillers(
    value: string,
    fillers?: Record<string, string>,
): string {
    if (!fillers) {
        return value;
    }

    let resolvedValue = value;

    for (const [key, fillerValue] of Object.entries(fillers)) {
        resolvedValue = resolvedValue.replace(`%${key}%`, fillerValue);
    }

    return resolvedValue;
}

export function getUiLabelKeyTail(key: string): string {
    const parts = key.split(".");
    return parts[parts.length - 1];
}

export function useUiLabelText(
    key: string,
    fillers?: Record<string, string>,
    localeOverride?: string,
) {
    const locale = useMemo(
        () => resolveUiLabelLocale(localeOverride),
        [localeOverride],
    );
    const {value} = useUiLabel(key, locale);
    const {value: enValue} = useUiLabel(key, "en");
    const finalValue = value ?? enValue;

    const rendered = useMemo(() => {
        if (finalValue === undefined) {
            return undefined;
        }

        return applyUiLabelFillers(finalValue, fillers);
    }, [fillers, finalValue]);

    return {
        locale,
        value,
        enValue,
        rendered,
    };
}

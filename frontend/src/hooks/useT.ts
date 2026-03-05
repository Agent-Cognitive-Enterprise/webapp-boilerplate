// /frontend/src/hooks/useT.ts

import { useMemo } from "react";
import { useUiLabel } from "./useUiLabel";

export function useT(
    k: string,
    fillers?: Record<string, string>,
    fallback?: string,
    localeOverride?: string,
): string {

    // Read locale once at component init
    const locale = useMemo(() =>
        localeOverride ||
        localStorage.getItem("uiLocale") ||
        navigator.language?.slice(0, 2) ||
        "en",
        [localeOverride]
    );

    // Subscribe to active locale
    const { value } = useUiLabel(k, locale);

    // Always subscribe to English fallback
    const { value: enValue } = useUiLabel(k, "en");

    const finalValue = value ?? enValue ?? fallback ?? k;

    // Apply fillers efficiently
    return useMemo(() => {
        let v = finalValue;
        if (!fillers) return v;

        for (const [fk, fv] of Object.entries(fillers)) {
            v = v.replace(`%${fk}%`, fv);
        }
        return v;

    }, [finalValue, fillers]);
}

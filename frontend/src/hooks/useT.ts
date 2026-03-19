import {useMemo} from "react";
import {useUiLabelText} from "./useUiLabelText";

export function useT(
    k: string,
    fillers?: Record<string, string>,
    fallback?: string,
    localeOverride?: string,
): string {
    const {rendered} = useUiLabelText(k, fillers, localeOverride);

    return useMemo(() => rendered ?? fallback ?? k, [fallback, k, rendered]);
}

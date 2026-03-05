// /frontend/src/hooks/useUiLabel.ts

import {useUiLabelContext} from "../contexts/UiLabelProvider.tsx";
import {useEffect, useMemo, useState} from "react";

export function useUiLabel(key: string, locale: string) {
    const ctx = useUiLabelContext();
    const [value, setValue] = useState<string | undefined>(() =>
        ctx.getValue(key, locale)
    );

    useEffect(() => {
        let cancelled = false;

        const unsubscribe = ctx.subscribe(key, locale, (v) => {
            if (!cancelled) setValue(v);
        });

        ctx.request(key, locale).then();

        setValue(ctx.getValue(key, locale));

        return () => {
            cancelled = true;
            unsubscribe();
        };
    }, [key, locale, ctx]);

    const suggest = useMemo(
        () => (newValue: string) => ctx.suggest(key, locale, newValue),
        [ctx, key, locale]
    );

    return {value, suggest};
}
// /frontend/src/hooks/useDebounce.ts

import {useRef, useEffect, useCallback} from "react";

export function useDebounce<T extends (...args: any[]) => void>(
    fn: T,
    delay: number
) {
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, []);

    return useCallback((...args: Parameters<T>) => {
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => fn(...args), delay);
    }, [fn, delay]);
}

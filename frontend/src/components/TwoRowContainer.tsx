// /frontend/src/components/TwoRowContainer.tsx

import React, {useCallback, useEffect, useMemo, useRef, useState} from "react";
import {getUserSettings, setUserSettings} from "../api/userSettings";

interface TwoRowContainerProps {
    top: React.ReactNode;
    down: React.ReactNode;
    parentUrl: string;
}

const SETTINGS_KEY = "twoRowSplit"; // persisted ratio (0..1)
const HANDLE_SIZE_PX = 8;
const MIN_TOP_PX = 120;
const MIN_DOWN_PX = 120;

const USER_SETTINGS_SUFFIX = "/two-row-split";

export default function TwoRowContainer({top, down, parentUrl}: TwoRowContainerProps) {
    const [ratio, setRatio] = useState<number>(0.5);
    const [settings, setSettings] = useState<Record<string, unknown>>({});
    const containerRef = useRef<HTMLDivElement | null>(null);
    const isDraggingRef = useRef(false);
    const containerBoxRef = useRef<DOMRect | null>(null);
    const [availableHeight, setAvailableHeight] = useState<number>(0);

    // Load saved ratio for this parentUrl
    useEffect(() => {
        let mounted = true;
        (async () => {
            try {
                const data = await getUserSettings(parentUrl + USER_SETTINGS_SUFFIX);
                const s = (data?.settings ?? {}) as Record<string, unknown>;
                if (!mounted) return;
                setSettings(s);
                const saved = s[SETTINGS_KEY];
                if (typeof saved === "number" && saved > 0 && saved < 1 && Number.isFinite(saved)) {
                    setRatio(clamp(saved, 0.05, 0.95));
                }
            } catch {
                // ignore load errors silently
            }
        })();
        return () => {
            mounted = false;
        };
    }, [parentUrl]);

    // Measure and keep container dimensions up to date
    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const measure = () => {
            const rect = el.getBoundingClientRect();
            containerBoxRef.current = rect;
            setAvailableHeight(Math.max(0, rect.height - HANDLE_SIZE_PX));
        };
        measure();
        const ro = new ResizeObserver(measure);
        ro.observe(el);
        return () => ro.disconnect();
    }, []);

    // Compute pixel heights based on ratio and current container size
    const {topPx, downPx} = useMemo(() => {
        const available = Math.max(0, availableHeight);
        const clampedTop = clamp(
            Math.round(available * ratio),
            MIN_TOP_PX,
            Math.max(MIN_TOP_PX, available - MIN_DOWN_PX)
        );
        return {
            topPx: clampedTop,
            downPx: Math.max(0, available - clampedTop),
        };
    }, [ratio, availableHeight]);

    const startDragging = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
        isDraggingRef.current = true;
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
        e.preventDefault();
    }, []);

    const stopDragging = useCallback(async () => {
        if (!isDraggingRef.current) return;
        isDraggingRef.current = false;
        try {
            const next = {...settings, [SETTINGS_KEY]: ratio};
            await setUserSettings(parentUrl + USER_SETTINGS_SUFFIX, next);
            setSettings(next);
        } catch {
            // ignore save errors silently
        }
    }, [parentUrl, ratio, settings]);

    const onPointerMove = useCallback((e: PointerEvent) => {
        if (!isDraggingRef.current) return;
        const rect = containerBoxRef.current;
        if (!rect || availableHeight <= 0) return;

        const offsetFromTop = e.clientY - rect.top;
        const clampedTop = clamp(
            offsetFromTop,
            MIN_TOP_PX,
            Math.max(MIN_TOP_PX, availableHeight - MIN_DOWN_PX)
        );
        const newRatio = clamp(clampedTop / availableHeight, 0.05, 0.95);
        setRatio(newRatio);
    }, [availableHeight]);

    useEffect(() => {
        const move = (e: PointerEvent) => onPointerMove(e);
        const up = () => stopDragging();
        window.addEventListener("pointermove", move);
        window.addEventListener("pointerup", up);
        window.addEventListener("pointercancel", up);
        return () => {
            window.removeEventListener("pointermove", move);
            window.removeEventListener("pointerup", up);
            window.removeEventListener("pointercancel", up);
        };
    }, [onPointerMove, stopDragging]);

    const onHandleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
        const step = 0.02;
        if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
            e.preventDefault();
            setRatio((r) => clamp(r + step, 0.05, 0.95));
        } else if (e.key === "ArrowDown" || e.key === "ArrowRight") {
            e.preventDefault();
            setRatio((r) => clamp(r - step, 0.05, 0.95));
        } else if (e.key === "Home" || e.key === "End") {
            e.preventDefault();
            setRatio(0.5);
        }
    };

    const onHandleDoubleClick = () => {
        const newRatio = 0.5;
        setRatio(newRatio);
        // Save immediately for convenience
        void (async () => {
            try {
                const next = {...settings, [SETTINGS_KEY]: newRatio};
                await setUserSettings(parentUrl + USER_SETTINGS_SUFFIX, next);
                setSettings(next);
            } catch {
                // ignore
            }
        })();
    };

    return (
        <>
            <div className="flex h-full w-full flex-col gap-3 lg:hidden">
                <div className="overflow-auto">{top}</div>
                <div className="overflow-auto">{down}</div>
            </div>
            <div
                ref={containerRef}
                className="relative hidden h-full w-full select-none lg:block"
            >
                {/* Top row */}
                <div
                    className="absolute left-0 right-0 top-0 overflow-auto"
                    style={{height: `${topPx}px`}}
                >
                    {top}
                </div>

                {/* Splitter */}
                <div
                    role="separator"
                    aria-orientation="horizontal"
                    tabIndex={0}
                    onPointerDown={startDragging}
                    onDoubleClick={onHandleDoubleClick}
                    onKeyDown={onHandleKeyDown}
                    className="absolute left-0 right-0 cursor-row-resize bg-gray-200 hover:bg-gray-300 active:bg-gray-400 transition-colors"
                    style={{top: `${topPx}px`, height: `${HANDLE_SIZE_PX}px`}}
                    title="Drag to resize. Double-click to reset to 50:50."
                />

                {/* Bottom row */}
                <div
                    className="absolute left-0 right-0 bottom-0 overflow-auto"
                    style={{top: `${topPx + HANDLE_SIZE_PX}px`, height: `${downPx}px`}}
                >
                    {down}
                </div>
            </div>
        </>
    );
}

function clamp(v: number, min: number, max: number) {
    return Math.min(max, Math.max(min, v));
}

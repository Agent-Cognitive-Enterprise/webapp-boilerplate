// /frontend/src/components/ThreeRowContainer.tsx

import React, {useEffect, useRef, useState} from "react";
import {getUserSettings, setUserSettings} from "../api/userSettings";
import {useDebounce} from "../hooks/useDebounce";

// Type for the row heights
type RowHeights = [number, number, number];

const MIN_ROW_HEIGHT = 10; // percent
const DEFAULT_HEIGHTS: RowHeights = [33.3, 33.3, 33.4];
const USER_SETTINGS_SUFFIX = "/three-row-heights";

const clamp = (val: number, min: number, max: number) =>
    Math.max(min, Math.min(max, val));

type ThreeRowContainerProps = {
    top: React.ReactNode;
    center: React.ReactNode;
    bottom: React.ReactNode;
    parentUrl: string;
};

const ThreeRowContainer: React.FC<ThreeRowContainerProps> = ({
                                                                 top,
                                                                 center,
                                                                 bottom,
                                                                 parentUrl,
                                                             }) => {
    const containerRef = useRef<HTMLDivElement | null>(null);

    const [heights, setHeights] = useState<RowHeights>(DEFAULT_HEIGHTS);
    const [loading, setLoading] = useState(true);

    // Drag state
    const draggingRef = useRef<0 | 1 | null>(null);
    const startYRef = useRef<number>(0);
    const startHeightsRef = useRef<RowHeights>(DEFAULT_HEIGHTS);

    // Load heights from user settings
    useEffect(() => {
        (async () => {
            try {
                const saved = await getUserSettings(parentUrl + USER_SETTINGS_SUFFIX);

                if (saved?.settings?.rowHeights) {
                    setHeights(saved.settings.rowHeights as RowHeights);
                } else {
                    setHeights(DEFAULT_HEIGHTS);
                }
            } catch {
                setHeights(DEFAULT_HEIGHTS);
            } finally {
                setLoading(false);
            }
        })();
    }, [parentUrl]);

    // Debounced save of settings
    const debouncedSave = useDebounce(async (newHeights: RowHeights) => {
        try {
            await setUserSettings(parentUrl + USER_SETTINGS_SUFFIX, {rowHeights: newHeights});
        } catch {
            // Optionally handle error
        }
    }, 500);

    // Drag handlers
    const onHandleDown = (index: 0 | 1) => (e: React.MouseEvent) => {
        if (!containerRef.current) return;
        draggingRef.current = index;
        startYRef.current = e.clientY;
        startHeightsRef.current = [...heights] as RowHeights;
        window.addEventListener("mousemove", onMouseMove);
        window.addEventListener("mouseup", onMouseUp);
        e.preventDefault();
    };

    const onHandleDoubleClick = () => {
        setHeights(DEFAULT_HEIGHTS);
        debouncedSave(DEFAULT_HEIGHTS);
    };

    const onHandleKeyDown = (index: 0 | 1) => (e: React.KeyboardEvent<HTMLDivElement>) => {
        const step = 2; // percent
        const [h0, h1, h2] = heights;
        let newHeights: RowHeights = [h0, h1, h2];

        if (e.key === "ArrowUp") {
            e.preventDefault();
            if (index === 0) {
                const newH0 = clamp(h0 - step, MIN_ROW_HEIGHT, h0 + h1 - MIN_ROW_HEIGHT);
                newHeights = [newH0, h0 + h1 - newH0, h2];
            } else {
                const newH1 = clamp(h1 - step, MIN_ROW_HEIGHT, h1 + h2 - MIN_ROW_HEIGHT);
                newHeights = [h0, newH1, h1 + h2 - newH1];
            }
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            if (index === 0) {
                const newH0 = clamp(h0 + step, MIN_ROW_HEIGHT, h0 + h1 - MIN_ROW_HEIGHT);
                newHeights = [newH0, h0 + h1 - newH0, h2];
            } else {
                const newH1 = clamp(h1 + step, MIN_ROW_HEIGHT, h1 + h2 - MIN_ROW_HEIGHT);
                newHeights = [h0, newH1, h1 + h2 - newH1];
            }
        } else if (e.key === "Home" || e.key === "End") {
            e.preventDefault();
            newHeights = DEFAULT_HEIGHTS;
        }

        if (newHeights !== heights) {
            setHeights(newHeights);
            debouncedSave(newHeights);
        }
    };

    const onMouseMove = (e: MouseEvent) => {
        if (!containerRef.current || draggingRef.current === null) return;

        const rect = containerRef.current.getBoundingClientRect();
        const deltaPx = e.clientY - startYRef.current;
        const deltaPct = (deltaPx / rect.height) * 100;

        const [h0s, h1s, h2s] = startHeightsRef.current;
        let newHeights: RowHeights = [h0s, h1s, h2s];

        if (draggingRef.current === 0) {
            const total = h0s + h1s;
            const newH0 = clamp(h0s + deltaPct, MIN_ROW_HEIGHT, total - MIN_ROW_HEIGHT);
            const newH1 = total - newH0;
            newHeights = [newH0, newH1, h2s];
        } else if (draggingRef.current === 1) {
            const total = h1s + h2s;
            const newH1 = clamp(h1s + deltaPct, MIN_ROW_HEIGHT, total - MIN_ROW_HEIGHT);
            const newH2 = total - newH1;
            newHeights = [h0s, newH1, newH2];
        }

        setHeights(newHeights);
        debouncedSave(newHeights);
    };

    const onMouseUp = () => {
        draggingRef.current = null;
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);
    };

    useEffect(() => {
        // Cleanup on unmounting
        return () => {
            window.removeEventListener("mousemove", onMouseMove);
            window.removeEventListener("mouseup", onMouseUp);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <>
            <div className="flex w-full flex-1 flex-col gap-3 lg:hidden">
                <div className="flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">{top}</div>
                <div className="flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">{center}</div>
                <div className="flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">{bottom}</div>
            </div>
            <div
                ref={containerRef}
                className="relative hidden h-full min-h-0 w-full flex-1 select-none transition-opacity duration-200 lg:flex lg:flex-col"
                style={{
                    opacity: loading ? 0.5 : 1,
                    pointerEvents: loading ? "none" : undefined,
                }}
            >
                {/* Row 1 */}
                <div
                    className="flex min-h-0 flex-col"
                    style={{
                        flexBasis: `${heights[0]}%`,
                        flexShrink: 0,
                    }}
                >
                    <div className="h-full flex-1 overflow-auto rounded-lg bg-gray-50/70 p-3 shadow-inner">
                        {top}
                    </div>
                </div>
                {/* Handle */}
                <div
                    role="separator"
                    aria-label="Resize Row 1 and 2"
                    tabIndex={0}
                    className="h-2 cursor-row-resize transition-colors hover:bg-gray-200"
                    style={{backgroundColor: "transparent"}}
                    onMouseDown={onHandleDown(0)}
                    onDoubleClick={onHandleDoubleClick}
                    onKeyDown={onHandleKeyDown(0)}
                />
                {/* Row 2 */}
                <div
                    className="flex min-h-0 flex-col"
                    style={{
                        flexBasis: `${heights[1]}%`,
                        flexShrink: 0,
                    }}
                >
                    <div className="h-full flex-1 overflow-auto rounded-lg bg-gray-50/70 p-3 shadow-inner">
                        {center}
                    </div>
                </div>
                {/* Handle */}
                <div
                    role="separator"
                    aria-label="Resize Row 2 and 3"
                    tabIndex={0}
                    className="h-2 cursor-row-resize transition-colors hover:bg-gray-200"
                    style={{backgroundColor: "transparent"}}
                    onMouseDown={onHandleDown(1)}
                    onDoubleClick={onHandleDoubleClick}
                    onKeyDown={onHandleKeyDown(1)}
                />
                {/* Row 3 */}
                <div
                    className="flex min-h-0 flex-1 flex-col"
                >
                    <div className="h-full flex-1 overflow-auto rounded-lg bg-gray-50/70 p-3 shadow-inner">
                        {bottom}
                    </div>
                </div>
            </div>
        </>
    );
};

export default ThreeRowContainer;

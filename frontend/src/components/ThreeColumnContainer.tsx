// /frontend/src/components/ThreeColumnContainer.tsx

import React, {useEffect, useRef, useState} from "react";
import {getUserSettings, setUserSettings} from "../api/userSettings";
import {useDebounce} from "../hooks/useDebounce";

// Type for the column widths
type ColumnWidths = [number, number, number];

const MIN_COL_WIDTH = 10; // percent
const DEFAULT_WIDTHS: ColumnWidths = [30, 50, 20];
const USER_SETTINGS_SUFFIX = "/three-column-widths";

const clamp = (val: number, min: number, max: number) =>
    Math.max(min, Math.min(max, val));

type ThreeColumnContainerProps = {
    left: React.ReactNode;
    center: React.ReactNode;
    right: React.ReactNode;
    parentUrl: string;
};

const ThreeColumnContainer: React.FC<ThreeColumnContainerProps> = ({
                                                                       left,
                                                                       center,
                                                                       right,
                                                                       parentUrl,
                                                                   }) => {
    const containerRef = useRef<HTMLDivElement | null>(null);

    const [widths, setWidths] = useState<ColumnWidths>(DEFAULT_WIDTHS);
    const [loading, setLoading] = useState(true);

    // Drag state
    const draggingRef = useRef<0 | 1 | null>(null);
    const startXRef = useRef<number>(0);
    const startWidthsRef = useRef<ColumnWidths>(DEFAULT_WIDTHS);

    // Load widths from user settings
    useEffect(() => {
        (async () => {
            try {
                const saved = await getUserSettings(parentUrl + USER_SETTINGS_SUFFIX);

                if (saved?.settings?.columnWidths) {
                    setWidths(saved.settings.columnWidths as ColumnWidths);
                } else {
                    setWidths(DEFAULT_WIDTHS);
                }
            } catch {
                setWidths(DEFAULT_WIDTHS);
            } finally {
                setLoading(false);
            }
        })();
    }, [parentUrl]);

    // Debounced save of settings
    const debouncedSave = useDebounce(async (newWidths: ColumnWidths) => {
        try {
            await setUserSettings(parentUrl + USER_SETTINGS_SUFFIX, {columnWidths: newWidths});
        } catch {
            // Optionally handle error
        }
    }, 500);

    // Drag handlers
    const onHandleDown = (index: 0 | 1) => (e: React.MouseEvent) => {
        if (!containerRef.current) return;
        draggingRef.current = index;
        startXRef.current = e.clientX;
        startWidthsRef.current = [...widths] as ColumnWidths;
        window.addEventListener("mousemove", onMouseMove);
        window.addEventListener("mouseup", onMouseUp);
        e.preventDefault();
    };

    const onMouseMove = (e: MouseEvent) => {
        if (!containerRef.current || draggingRef.current === null) return;

        const rect = containerRef.current.getBoundingClientRect();
        const deltaPx = e.clientX - startXRef.current;
        const deltaPct = (deltaPx / rect.width) * 100;

        const [w0s, w1s, w2s] = startWidthsRef.current;
        let newWidths: ColumnWidths = [w0s, w1s, w2s];

        if (draggingRef.current === 0) {
            const total = w0s + w1s;
            const newW0 = clamp(w0s + deltaPct, MIN_COL_WIDTH, total - MIN_COL_WIDTH);
            const newW1 = total - newW0;
            newWidths = [newW0, newW1, w2s];
        } else if (draggingRef.current === 1) {
            const total = w1s + w2s;
            const newW1 = clamp(w1s + deltaPct, MIN_COL_WIDTH, total - MIN_COL_WIDTH);
            const newW2 = total - newW1;
            newWidths = [w0s, newW1, newW2];
        }

        setWidths(newWidths);
        debouncedSave(newWidths);
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
                <div className="flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">{left}</div>
                <div className="flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">{center}</div>
                <div className="flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">{right}</div>
            </div>
            <div
                ref={containerRef}
                className="relative hidden h-full min-h-0 w-full flex-1 select-none transition-opacity duration-200 lg:flex"
                style={{
                    opacity: loading ? 0.5 : 1,
                    pointerEvents: loading ? "none" : undefined,
                }}
            >
                {/* Column 1 */}
                <div
                    className="flex min-w-0 flex-col"
                    style={{
                        flexBasis: `${widths[0]}%`,
                        flexShrink: 0,
                    }}
                >
                    <div className="h-full flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">
                        {left}
                    </div>
                </div>
                {/* Handle */}
                <div
                    role="separator"
                    aria-label="Resize Column 1 and 2"
                    className="w-2 cursor-col-resize"
                    style={{backgroundColor: "transparent"}}
                    onMouseDown={onHandleDown(0)}
                />
                {/* Column 2 */}
                <div
                    className="flex min-w-0 flex-col"
                    style={{
                        flexBasis: `${widths[1]}%`,
                        flexShrink: 0,
                    }}
                >
                    <div className="h-full flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">
                        {center}
                    </div>
                </div>
                {/* Handle */}
                <div
                    role="separator"
                    aria-label="Resize Column 2 and 3"
                    className="w-2 cursor-col-resize"
                    style={{backgroundColor: "transparent"}}
                    onMouseDown={onHandleDown(1)}
                />
                {/* Column 3 */}
                <div
                    className="flex flex-1 flex-col"
                    style={{marginRight: "5px"}}
                >
                    <div className="h-full flex-1 rounded-lg bg-gray-50/70 p-3 shadow-inner">
                        {right}
                    </div>
                </div>
            </div>
        </>
    );
};

export default ThreeColumnContainer;

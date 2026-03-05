// /frontend/src/components/UiLabel.tsx

import React, {type JSX, useMemo, useState} from "react";
import {useUiLabelContext} from "../contexts/UiLabelProvider.tsx";
import {TranslationModal} from "./modal/TranslationModal";
import {useUiLabel} from "../hooks/useUiLabel.ts";

interface UiLabelProps {
    k: string;
    fillers?: Record<string, string>;
    className?: string;
    as?: keyof JSX.IntrinsicElements;
}

export default function UiLabel({
    k,
    fillers,
    className,
    as: Tag = "span"
}: UiLabelProps) {

    // Read the current locale from localStorage, fallback to browser language or 'en'
    const locale = useMemo(() =>
        localStorage.getItem("uiLocale") || navigator.language?.slice(0,2) || "en",
        []
    );
    // Subscribe to the target locale, live updates will be handled automatically
    const {value} = useUiLabel(k, locale);
    // Also, subscribe to English so we can render immediately if the target locale is missing
    const {value: enValue} = useUiLabel(k, "en");
    const {request} = useUiLabelContext();


    // Prefer target locale value; fallback to live English subscription value
    const finalValue = value ?? enValue;

    const [showModal, setShowModal] = useState(false);

    // ------------------------------------------
    // 1. BLURRED TAIL WHEN VALUE IS NOT LOADED
    // ------------------------------------------
    const blurredKeyTail = useMemo(() => {
        const parts = k.split(".");
        return parts[parts.length - 1];
    }, [k]);

    // ------------------------------------------
    // 2. NORMAL TRANSLATION + FILLERS
    // ------------------------------------------
    const rendered = useMemo(() => {

        const v = finalValue;

        if (v === undefined) return undefined;

        if (!fillers) return v;

        let text = v;
        for (const [fk, fv] of Object.entries(fillers)) {
            text = text.replace(`%${fk}%`, fv);
        }
        return text;
    }, [finalValue, fillers]);

    const onRightClick = (e: React.MouseEvent) => {
        e.preventDefault();
        request(k, "en").then(); // ensure English base is fetched
        setShowModal(true);
    };

    return (
        <>
            <Tag
                className={
                    (className ? className : "") +
                    (rendered === undefined ? " opacity-20 blur-[2px] select-none" : "")
                }
                onContextMenu={onRightClick}
            >
                {rendered ?? blurredKeyTail}
            </Tag>

            {showModal && (
                <TranslationModal
                    keyName={k}
                    locale={locale}
                    currentValue={value ?? ""}
                    englishValue={enValue ?? ""}
                    onClose={() => setShowModal(false)}
                />
            )}
        </>
    );
}

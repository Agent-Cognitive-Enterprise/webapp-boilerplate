// /frontend/src/components/UiLabel.tsx

import React, {type JSX, useMemo, useState} from "react";
import {useUiLabelContext} from "../contexts/UiLabelProvider.tsx";
import {TranslationModal} from "./modal/TranslationModal";
import {getUiLabelKeyTail, useUiLabelText} from "../hooks/useUiLabelText.ts";

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
    const {locale, value, enValue, rendered} = useUiLabelText(k, fillers);
    const {request} = useUiLabelContext();

    const [showModal, setShowModal] = useState(false);

    const blurredKeyTail = useMemo(() => getUiLabelKeyTail(k), [k]);

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

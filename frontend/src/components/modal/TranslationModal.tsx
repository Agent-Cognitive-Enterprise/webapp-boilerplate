// /frontend/src/components/modal/TranslationModal.tsx

import {useMemo, useEffect, useRef, useState, useContext} from "react";
import {useUiLabelContext} from "../../contexts/UiLabelProvider.tsx";
import {AuthContext} from "../../contexts/AuthContext.tsx";
import {useUiLabel} from "../../hooks/useUiLabel.ts";
import UiLabel from "../UiLabel.tsx";
import {createPortal} from "react-dom";
import {useT} from "../../hooks/useT.ts";

interface Props {
    keyName: string;
    locale: string;
    // optional legacy props; live values are fetched inside the modal
    englishValue?: string;
    currentValue?: string;
    onClose: () => void;
}

export function TranslationModal(props: Props) {
    return createPortal(
        <ModalContent {...props} />,
        document.body
    );
}

function ModalContent(
    {
        keyName,
        locale,
        englishValue,
        currentValue,
        onClose
    }: Props
) {
    const auth = useContext(AuthContext);
    if (!auth) throw new Error("AuthContext not available");
    const {token} = auth;

    const ctx = useUiLabelContext();

    // Live values via subscription
    const {value: enLive} = useUiLabel(keyName, "en");
    const {value: curLive} = useUiLabel(keyName, locale);

    // Track if the user edited the textarea to avoid clobbering input on updates
    const userEditedRef = useRef(false);
    const [text, setText] = useState<string>(currentValue ?? curLive ?? "");


    useEffect(() => {
        if (!userEditedRef.current) {
            // Initialise/refresh from server/current only if the user hasn't typed
            if ((text ?? "") === "" && (curLive ?? "") !== "") {
                setText(curLive!);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [curLive]);

    const onSubmit = () => {
        ctx.suggest(keyName, locale, text).then();
        onClose();
    };
    const keyText = useT("translation_modal.label.key", undefined, "Key", locale);
    const loadingText = useT("common.loading", undefined, "Loading...", locale);

    const keyNameTail = useMemo(() => {
        const parts = keyName.split(".");
        return parts[parts.length - 1];
    }, [keyName]);

    // If no token, do not render the modal
    if (!token) return null;

    return (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30 z-50 backdrop-blur-md">
            <div
                className="
            bg-white
            rounded-lg
            p-8
            w-11/12
            max-w-4xl
            shadow-2xl

            /* RESET inherited styles */
            text-base
            text-black
            font-sans
            isolation-isolate
            leading-normal
        "
            >
                <h3 className="text-2xl font-bold mb-6 text-gray-900 text-center">
                    <UiLabel k="translation_modal.title.suggest_translation"/>
                </h3>

                <div className="flex flex-col gap-4 mb-6 text-base text-black">
                    <label className="font-semibold text-gray-700">
                        {keyText}:
                    </label>
                    <div className="w-full px-4 py-3 border border-gray-300 rounded-md bg-gray-100 text-lg">
                        {keyNameTail}
                    </div>

                    <div className="text-gray-700">
                        <label className="font-semibold">en:</label>
                        <div className="w-full px-4 py-3 border border-gray-300 rounded-md bg-gray-100 text-lg">
                            {enLive || englishValue || `(${loadingText})`}
                        </div>
                    </div>

                    <div className="text-gray-700">
                        <label className="font-semibold">{locale}:</label>
                        <textarea
                            value={text}
                            onChange={(e) => {
                                userEditedRef.current = true;
                                setText(e.target.value);
                            }}
                            className="w-full px-4 py-3 border border-gray-300 rounded-md bg-gray-100
                        focus:ring-blue-500
                        focus:outline-none
                        resize-none
                        text-lg
                        text-black
                    "
                            rows={8}
                        />
                    </div>
                </div>

                <div className="flex justify-between mt-4">
                    <button
                        onClick={onClose}
                        className="
                    px-5 py-2.5
                    rounded
                    bg-gray-200
                    hover:bg-gray-300
                    text-black
                    font-medium
                "
                    >
                        <UiLabel k="button.cancel"/>
                    </button>
                    <button
                        onClick={onSubmit}
                        className="
                    px-5 py-2.5
                    rounded
                    bg-blue-600
                    text-white
                    hover:bg-blue-700
                    font-medium
                "
                    >
                        <UiLabel k="button.submit"/>
                    </button>
                </div>
            </div>
        </div>

    );
}

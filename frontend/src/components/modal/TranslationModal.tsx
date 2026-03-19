// /frontend/src/components/modal/TranslationModal.tsx

import UiLabel from "../UiLabel.tsx";
import {createPortal} from "react-dom";
import {useT} from "../../hooks/useT.ts";
import {useTranslationModalState} from "./translationModal/useTranslationModalState.ts";

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
    const {
        token,
        englishValue: englishLiveValue,
        keyNameTail,
        text,
        setDraftValue,
        submitSuggestion,
    } = useTranslationModalState({
        keyName,
        locale,
        currentValue,
    });

    const onSubmit = () => {
        submitSuggestion().then(() => {
            onClose();
        });
    };
    const keyText = useT("translation_modal.label.key", undefined, "Key", locale);
    const loadingText = useT("common.loading", undefined, "Loading...", locale);

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
                            {englishLiveValue || englishValue || `(${loadingText})`}
                        </div>
                    </div>

                    <div className="text-gray-700">
                        <label className="font-semibold">{locale}:</label>
                        <textarea
                            value={text}
                            onChange={(e) => {
                                setDraftValue(e.target.value);
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

// /frontend/src/components/modal/LocaleSelector.tsx

import {createPortal} from "react-dom";
import {useEffect, useState} from "react";
import {localeLabels} from "../localeUtils";
import UiLabel from "../UiLabel.tsx";

interface Props {
    locales: string[];
    loading: boolean;
    selected: string;
    onClose: () => void;
    onSelect: (locale: string) => void;
}

export default function SelectLocaleModal(props: Props) {
    return createPortal(
        <ModalContent {...props} />,
        document.body
    );
}

function ModalContent(
    {
        locales,
        loading,
        selected,
        onClose,
        onSelect,
    }: Props
) {
    // Temporary selection inside the modal; only applied on Save
    const [tempSelected, setTempSelected] = useState<string>(selected);

    // Keep internal selection in sync if the prop changes while the modal is open
    useEffect(() => {
        setTempSelected(selected);
    }, [selected]);

    const handleSave = () => {
        const value = tempSelected || selected;
        onSelect(value);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex justify-center items-center">
            {/* Background overlay (separate from flex container children) */}
            <div className="absolute inset-0 bg-black/30 backdrop-blur-md"/>

            {/* Modal content container */}
            <div
                className="relative bg-white/50 backdrop-blur-md rounded-lg p-8 w-4/5 max-w-2xl shadow-md
                           transform transition-all duration-300 hover:scale-105 hover:shadow-xl z-10"
            >
                <h3 className="text-xl font-bold mb-4 text-gray-800 text-center">
                    <UiLabel k="locale_selector.title.select_language"/>
                </h3>

                {loading ? (
                    <div className="py-6 text-center text-gray-500">
                        <UiLabel k="common.loading"/>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-h-[60vh] overflow-y-auto pr-2">
                        {locales.map((loc) => {
                            const isSelected = loc === tempSelected;
                            return (
                                <button
                                    key={loc}
                                    onClick={() => setTempSelected(loc)}
                                    className={`flex flex-col items-center p-3 border rounded-lg transition text-center
                                    ${isSelected ? "bg-blue-100 border-blue-400" : "hover:bg-gray-100"}`}
                                >
                                    <span className="text-sm font-bold text-black">
                                        {localeLabels[loc] ?? loc}
                                    </span>
                                    <span className="text-xl text-gray-500 mt-1">
                                        {loc}
                                    </span>
                                </button>
                            );
                        })}
                    </div>
                )}

                {/* Footer actions */}
                <div className="flex justify-between mt-6">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-300 rounded-md hover:bg-gray-400
                        transition-colors font-semibold"
                    >
                        <UiLabel k="button.cancel"/>
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600
                        transition-colors font-semibold"
                    >
                        <UiLabel k="button.save"/>
                    </button>
                </div>
            </div>
        </div>
    );
}

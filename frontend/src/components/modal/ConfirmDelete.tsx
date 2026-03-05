// /frontend/src/components/modal/ConfirmDelete.tsx
// noinspection DuplicatedCode

import {useState, useEffect} from "react";
import UiLabel from "../UiLabel.tsx";
import {useT} from "../../hooks/useT.ts";

interface ConfirmDeleteProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title?: string; // chapter title
}

export default function ConfirmDeleteModal(
    {
        isOpen,
        onClose,
        onConfirm,
        title
    }: ConfirmDeleteProps
) {
    const [code, setCode] = useState("");
    const [input, setInput] = useState("");
    const [valid, setValid] = useState(false);
    const placeholderEnterCodeHere = useT("confirm_delete_modal.placeholder.enter_code_here");

    useEffect(() => {
        if (isOpen) {
            const randomCode = Math.floor(1000 + Math.random() * 9000).toString();
            setCode(randomCode);
            setInput("");
            setValid(false);
        }
    }, [isOpen]);

    useEffect(() => {
        setValid(input === code);
    }, [input, code]);

    if (!isOpen) return null;

    const handleConfirm = () => {
        if (!valid) return;
        onConfirm();
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex justify-center items-center">
            <div
                className="absolute inset-0 bg-black/30 backdrop-blur-md"
                onClick={onClose}
            />
            <div
                className="relative bg-white/50 backdrop-blur-md rounded-lg p-8 w-full max-w-sm shadow-md transform
                transition-all duration-300 hover:scale-105 hover:shadow-xl z-10">

                {title && (
                    <h3 className="text-2xl font-bold mb-4 text-center text-gray-800 truncate overflow-hidden whitespace-nowrap">
                        {title}
                    </h3>
                )}

                <p className="mb-4 text-gray-700 text-center">
                    <UiLabel k="confirm_delete_modal.description.to_confirm_deletion_type_the_following_number"/>
                </p>
                <p className="mb-6 text-center font-mono text-lg bg-gray-100 py-2 rounded">
                    {code}
                </p>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={placeholderEnterCodeHere}
                    autoFocus
                    className="w-full mb-6 px-4 py-2 border border-gray-300 rounded-md focus:outline-none
                    focus:ring-2 focus:ring-blue-400  text-gray-800 bg-gray-100 text-center text-lg"
                />
                <div className="flex justify-between gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-md font-semibold bg-gray-200 text-gray-800 hover:bg-gray-300
                        transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
                    >
                        <UiLabel k="button.cancel"/>
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={!valid}
                        className={`px-4 py-2 rounded-md font-semibold transition-colors focus:outline-none 
                        focus:ring-2 ${
                            valid
                                ? "bg-red-500 text-white hover:bg-red-600 focus:ring-red-400"
                                : "bg-gray-200 text-gray-500 cursor-not-allowed focus:ring-gray-300"
                        }`}
                    >
                        <UiLabel k="button.delete"/>
                    </button>
                </div>
            </div>
        </div>
    );
}

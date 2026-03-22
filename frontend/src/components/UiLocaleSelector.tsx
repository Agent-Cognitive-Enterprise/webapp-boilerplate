// /frontend/src/components/UiLocaleSelector.tsx
import {useContext, useEffect, useState} from "react";
import SelectLocaleModal from "./modal/SelectLocale.tsx";
import api from "../api/api";
import {localeLabels} from "./localeUtils";
import { setSavedUiLocalePreference } from "../api/userSettings.ts";
import { persistActiveUiLocale } from "../i18n/localeDirection.ts";
import { getPreferredUiLocale } from "../i18n/uiLocale.ts";
import { AuthContext } from "../contexts/AuthContext.tsx";

export default function LocaleSelector() {
    const auth = useContext(AuthContext);
    const [modalOpen, setModalOpen] = useState(false);
    const [locales, setLocales] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);

    // Start with saved locale or browser default
    const currentLocale = getPreferredUiLocale();

    useEffect(() => {
        async function loadLocales() {
            try {
                const resp = await api.post(
                    "/ui-label",
                    {
                        action: "list"
                    },
                    {
                        headers: {
                            "Content-Type": "application/json",
                        },
                    }
                );
                const data = resp?.data?.data ?? resp?.data ?? [];
                setLocales(Array.isArray(data) ? data : data.locales || []);
            } catch (err) {
                console.error("Failed to load locales", err);
            } finally {
                setLoading(false);
            }
        }

        loadLocales().then();
    }, []);

    async function handleSelectLocale(loc: string) {
        persistActiveUiLocale(loc);
        if (auth?.token) {
            await setSavedUiLocalePreference(loc);
        }
        // Reload the page immediately to apply locale globally
        window.location.reload();
    }

    return (
        <>
            <div
                onClick={() => setModalOpen(true)}
                className="ace-input cursor-pointer text-left hover:bg-slate-50 transition"
            >
                {localeLabels[currentLocale] ?? currentLocale}
            </div>

            {modalOpen && (
                <SelectLocaleModal
                    locales={locales}
                    loading={loading}
                    selected={currentLocale}
                    onClose={() => setModalOpen(false)}
                    onSelect={handleSelectLocale}
                />
            )}
        </>
    );
}

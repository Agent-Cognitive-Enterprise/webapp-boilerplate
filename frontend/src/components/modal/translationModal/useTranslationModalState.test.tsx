import {renderHook, act} from "@testing-library/react";
import {beforeEach, describe, expect, it, vi} from "vitest";
import React from "react";
import {AuthContext} from "../../../contexts/AuthContext.tsx";
import {useTranslationModalState} from "./useTranslationModalState";
import {useUiLabelContext} from "../../../contexts/UiLabelProvider.tsx";
import {useUiLabel} from "../../../hooks/useUiLabel.ts";

vi.mock("../../../contexts/UiLabelProvider.tsx", () => ({
    useUiLabelContext: vi.fn(),
}));

vi.mock("../../../hooks/useUiLabel.ts", () => ({
    useUiLabel: vi.fn(),
}));

function buildWrapper(token: string | null) {
    return function Wrapper({children}: {children: React.ReactNode}) {
        return (
            <AuthContext.Provider
                value={{
                    token,
                    user: null,
                    login: vi.fn(),
                    register: vi.fn(),
                    logout: vi.fn(),
                    setToken: vi.fn(),
                }}
            >
                {children}
            </AuthContext.Provider>
        );
    };
}

describe("useTranslationModalState", () => {
    const suggest = vi.fn().mockResolvedValue(undefined);

    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(useUiLabelContext).mockReturnValue({
            suggest,
            request: vi.fn(),
            getValue: vi.fn(),
            subscribe: vi.fn(),
        } as never);
    });

    it("seeds english and locale live values and submits the current draft", async () => {
        vi.mocked(useUiLabel).mockImplementation((key: string, locale: string) => {
            if (locale === "en") {
                return {value: `EN:${key}`} as never;
            }

            return {value: `FR:${key}`} as never;
        });

        const {result} = renderHook(
            () =>
                useTranslationModalState({
                    keyName: "profile.label.full_name",
                    locale: "fr",
                }),
            {wrapper: buildWrapper("token-123")},
        );

        expect(result.current.keyNameTail).toBe("full_name");
        expect(result.current.englishValue).toBe("EN:profile.label.full_name");
        expect(result.current.localeValue).toBe("FR:profile.label.full_name");
        expect(result.current.text).toBe("FR:profile.label.full_name");

        act(() => {
            result.current.setDraftValue("Nom modifie");
        });

        await act(async () => {
            await result.current.submitSuggestion();
        });

        expect(suggest).toHaveBeenCalledWith("profile.label.full_name", "fr", "Nom modifie");
    });

    it("does not clobber the draft after the user edits it", async () => {
        let localeValue = "Nom initial";

        vi.mocked(useUiLabel).mockImplementation((_key: string, locale: string) => {
            if (locale === "en") {
                return {value: "Full Name"} as never;
            }

            return {value: localeValue} as never;
        });

        const {result, rerender} = renderHook(
            () =>
                useTranslationModalState({
                    keyName: "profile.label.full_name",
                    locale: "fr",
                }),
            {wrapper: buildWrapper("token-123")},
        );

        expect(result.current.text).toBe("Nom initial");

        act(() => {
            result.current.setDraftValue("Nom utilisateur");
        });

        localeValue = "Nom serveur";
        rerender();

        expect(result.current.text).toBe("Nom utilisateur");
    });
});

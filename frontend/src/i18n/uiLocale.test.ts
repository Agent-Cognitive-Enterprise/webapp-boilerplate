import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
    getNavigatorUiLocale,
    getPreferredUiLocale,
    getStoredUiLocale,
    setStoredUiLocale,
} from "./uiLocale.ts";

describe("uiLocale helpers", () => {
    beforeEach(() => {
        localStorage.clear();
        vi.stubGlobal("navigator", {
            ...navigator,
            language: "fr-FR",
        });
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("reads and normalizes the stored locale", () => {
        localStorage.setItem("uiLocale", "ar_EG");

        expect(getStoredUiLocale()).toBe("ar");
    });

    it("prefers the explicit override, then storage, then navigator locale", () => {
        localStorage.setItem("uiLocale", "de-DE");

        expect(getPreferredUiLocale("sk-SK")).toBe("sk");
        expect(getPreferredUiLocale()).toBe("de");

        localStorage.removeItem("uiLocale");
        expect(getPreferredUiLocale()).toBe("fr");
        expect(getNavigatorUiLocale()).toBe("fr");
    });

    it("stores normalized locale values", () => {
        expect(setStoredUiLocale("EN_us")).toBe("en");
        expect(localStorage.getItem("uiLocale")).toBe("en");
    });
});

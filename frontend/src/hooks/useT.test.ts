import {renderHook} from "@testing-library/react";
import {beforeEach, describe, expect, it, vi} from "vitest";
import {useT} from "./useT";
import {useUiLabel} from "./useUiLabel";

vi.mock("./useUiLabel", () => ({
    useUiLabel: vi.fn(),
}));

describe("useT", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
        localStorage.setItem("uiLocale", "fr");
    });

    it("uses the active locale value, falls back to english, and applies fillers", () => {
        vi.mocked(useUiLabel).mockImplementation((key: string, locale: string) => {
            if (key !== "greeting.message") {
                return {value: undefined} as never;
            }

            if (locale === "fr") {
                return {value: undefined} as never;
            }

            return {value: "Hello %name%"} as never;
        });

        const {result} = renderHook(() =>
            useT("greeting.message", {name: "Alice"}, "Fallback message"),
        );

        expect(result.current).toBe("Hello Alice");
    });

    it("uses the override locale before local storage", () => {
        vi.mocked(useUiLabel).mockImplementation((_key: string, locale: string) => {
            if (locale === "de") {
                return {value: "Hallo"} as never;
            }

            return {value: "Hello"} as never;
        });

        const {result} = renderHook(() => useT("greeting.message", undefined, undefined, "de"));

        expect(result.current).toBe("Hallo");
    });
});

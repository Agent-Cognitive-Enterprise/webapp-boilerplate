import {renderHook} from "@testing-library/react";
import {beforeEach, describe, expect, it, vi} from "vitest";
import {useUiLabel} from "./useUiLabel";
import {useUiLabelContext} from "../contexts/UiLabelProvider.tsx";

vi.mock("../contexts/UiLabelProvider.tsx", () => ({
    useUiLabelContext: vi.fn(),
}));

describe("useUiLabel", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("uses the provider subscription to seed and update the value while issuing one initial request", () => {
        const request = vi.fn().mockResolvedValue(undefined);
        const getValue = vi.fn().mockReturnValue("Cached value");
        const subscribe = vi.fn((key: string, locale: string, cb: (value: string | undefined) => void) => {
            cb(`Live value for ${key}:${locale}`);
            return vi.fn();
        });

        vi.mocked(useUiLabelContext).mockReturnValue({
            getValue,
            subscribe,
            request,
            suggest: vi.fn(),
        } as never);

        const {result} = renderHook(() => useUiLabel("greeting.hello", "fr"));

        expect(getValue).toHaveBeenCalledWith("greeting.hello", "fr");
        expect(subscribe).toHaveBeenCalledWith("greeting.hello", "fr", expect.any(Function));
        expect(request).toHaveBeenCalledWith("greeting.hello", "fr");
        expect(result.current.value).toBe("Live value for greeting.hello:fr");
    });

    it("binds suggest to the current key and locale", async () => {
        const suggest = vi.fn().mockResolvedValue(undefined);

        vi.mocked(useUiLabelContext).mockReturnValue({
            getValue: vi.fn(),
            subscribe: vi.fn(() => vi.fn()),
            request: vi.fn().mockResolvedValue(undefined),
            suggest,
        } as never);

        const {result} = renderHook(() => useUiLabel("greeting.hello", "fr"));

        await result.current.suggest("Bonjour");

        expect(suggest).toHaveBeenCalledWith("greeting.hello", "fr", "Bonjour");
    });
});

import {describe, expect, it, vi} from "vitest";

import {pollUntilUiLabelAvailable} from "./polling";

describe("ui label polling", () => {
    it("polls until the requested value appears and then notifies listeners", async () => {
        let currentValue: string | undefined;
        const fetchLocaleIfStale = vi.fn(async () => {
            currentValue = "Bonjour";
        });
        const notify = vi.fn();

        await expect(
            pollUntilUiLabelAvailable({
                key: "greeting.hello",
                locale: "fr",
                maxAttempts: 3,
                intervalMs: 100,
                fetchLocaleIfStale,
                getValue: () => currentValue,
                notify,
                wait: async () => undefined,
            }),
        ).resolves.toBe(true);

        expect(fetchLocaleIfStale).toHaveBeenCalledWith("fr");
        expect(notify).toHaveBeenCalledWith("greeting.hello", "fr");
    });

    it("returns false when the value never appears", async () => {
        const fetchLocaleIfStale = vi.fn(async () => undefined);
        const notify = vi.fn();

        await expect(
            pollUntilUiLabelAvailable({
                key: "greeting.hello",
                locale: "fr",
                maxAttempts: 2,
                intervalMs: 100,
                fetchLocaleIfStale,
                getValue: () => undefined,
                notify,
                wait: async () => undefined,
            }),
        ).resolves.toBe(false);

        expect(fetchLocaleIfStale).toHaveBeenCalledTimes(2);
        expect(notify).not.toHaveBeenCalled();
    });
});

import {describe, expect, it, vi, beforeEach} from "vitest";
import {
    loadUiLabelLocalCache,
    readUiLabelValue,
    replaceUiLabelLocaleCache,
    touchUiLabelLocaleLastCheck,
    UI_LABEL_LOCAL_STORAGE_KEY,
} from "./cache";
import type {UiLabelLocalCache} from "./types";

describe("ui label cache helpers", () => {
    beforeEach(() => {
        vi.restoreAllMocks();
        localStorage.clear();
    });

    it("hydrates a cached value into memory on read", () => {
        const memoryCache = new Map<string, string>();
        const localCache: UiLabelLocalCache = {
            fr: {
                values: {
                    "greeting.hello": "Bonjour",
                },
                values_hash: "hash-fr",
                last_check: 123,
            },
        };

        expect(readUiLabelValue(memoryCache, localCache, "greeting.hello", "fr")).toBe("Bonjour");
        expect(memoryCache.get("greeting.hello::fr")).toBe("Bonjour");
    });

    it("replaces locale cache and updates last_check metadata", () => {
        const memoryCache = new Map<string, string>();
        const localCache: UiLabelLocalCache = {};
        const notify = vi.fn();

        replaceUiLabelLocaleCache(
            memoryCache,
            localCache,
            "fr",
            {"greeting.hello": "Bonjour"},
            notify,
            "hash-fr",
        );
        touchUiLabelLocaleLastCheck(localCache, "fr");

        const savedCache = loadUiLabelLocalCache();

        expect(savedCache.fr?.values["greeting.hello"]).toBe("Bonjour");
        expect(savedCache.fr?.values_hash).toBe("hash-fr");
        expect(savedCache.fr?.last_check).toEqual(expect.any(Number));
        expect(memoryCache.get("greeting.hello::fr")).toBe("Bonjour");
        expect(notify).toHaveBeenCalledWith("greeting.hello", "fr");
        expect(localStorage.getItem(UI_LABEL_LOCAL_STORAGE_KEY)).toContain("Bonjour");
    });
});

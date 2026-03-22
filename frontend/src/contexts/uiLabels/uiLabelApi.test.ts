import {beforeEach, describe, expect, it, vi} from "vitest";

import api from "../../api/api";
import {
    fetchUiLabelLocale,
    normalizeUiLabelFetchPayload,
    suggestUiLabelValue,
} from "./uiLabelApi";

vi.mock("../../api/api", () => ({
    default: {
        post: vi.fn(),
    },
}));

describe("ui label api helpers", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("normalizes nested labels payloads with values hash", () => {
        expect(
            normalizeUiLabelFetchPayload(
                {
                    data: {
                        labels: {
                            "greeting.hello": "Bonjour",
                        },
                        values_hash: "hash-fr",
                    },
                },
                "hash-old",
            ),
        ).toEqual({
            kind: "labels",
            labels: {
                "greeting.hello": "Bonjour",
            },
            valuesHash: "hash-fr",
        });
    });

    it("fetches locale labels and normalizes array responses", async () => {
        vi.mocked(api.post).mockResolvedValue({
            data: [
                {key: "greeting.hello", value: "Bonjour"},
                {key: "greeting.goodbye", value: "Au revoir"},
            ],
        });

        await expect(fetchUiLabelLocale("fr", "hash-fr")).resolves.toEqual({
            kind: "labels",
            labels: {
                "greeting.hello": "Bonjour",
                "greeting.goodbye": "Au revoir",
            },
            valuesHash: "hash-fr",
        });
        expect(api.post).toHaveBeenCalledWith(
            "/ui-label",
            {
                action: "get",
                locale: "fr",
                values_hash: "hash-fr",
            },
            expect.objectContaining({
                headers: expect.objectContaining({
                    "Content-Type": "application/json",
                }),
            }),
        );
    });

    it("rejects unauthorized suggestions before calling the API", async () => {
        await expect(
            suggestUiLabelValue(null, "greeting.hello", "fr", "Bonjour"),
        ).rejects.toThrow("Unauthorized");
        expect(api.post).not.toHaveBeenCalled();
    });
});

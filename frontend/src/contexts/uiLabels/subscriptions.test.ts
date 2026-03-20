import {describe, expect, it, vi} from "vitest";

import {
    notifyUiLabelListeners,
    subscribeUiLabelListener,
    type UiLabelSubscriptions,
} from "./subscriptions";

describe("ui label subscriptions", () => {
    it("notifies listeners and ignores listener errors", () => {
        const subscriptions: UiLabelSubscriptions = new Map();
        const healthyListener = vi.fn();
        const throwingListener = vi.fn(() => {
            throw new Error("listener failure");
        });

        subscribeUiLabelListener(subscriptions, "greeting.hello", "fr", healthyListener);
        subscribeUiLabelListener(subscriptions, "greeting.hello", "fr", throwingListener);

        expect(() => {
            notifyUiLabelListeners(subscriptions, () => "Bonjour", "greeting.hello", "fr");
        }).not.toThrow();
        expect(healthyListener).toHaveBeenCalledWith("Bonjour");
        expect(throwingListener).toHaveBeenCalledWith("Bonjour");
    });

    it("cleans up empty key and locale maps on unsubscribe", () => {
        const subscriptions: UiLabelSubscriptions = new Map();
        const unsubscribe = subscribeUiLabelListener(
            subscriptions,
            "greeting.hello",
            "fr",
            vi.fn(),
        );

        expect(subscriptions.get("fr")?.has("greeting.hello")).toBe(true);

        unsubscribe();

        expect(subscriptions.has("fr")).toBe(false);
    });
});

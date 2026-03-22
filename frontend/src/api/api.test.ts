import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../auth/sessionEvents.ts", () => ({
    notifySessionInvalidated: vi.fn(),
}));

import api from "./api";
import { notifySessionInvalidated } from "../auth/sessionEvents.ts";

describe("api interceptor", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        sessionStorage.clear();
    });

    it("notifies session invalidation when refresh fails after a 401", async () => {
        const refreshError = new Error("refresh failed");
        vi.spyOn(api, "post").mockRejectedValue(refreshError);

        const rejectedHandler = (api.interceptors.response as any).handlers[0].rejected as (error: unknown) => Promise<unknown>;

        const requestError = {
            config: {
                url: "/users/me/",
                headers: {},
            },
            response: {
                status: 401,
            },
        };

        await expect(rejectedHandler(requestError)).rejects.toBe(refreshError);

        expect(notifySessionInvalidated).toHaveBeenCalledWith("refresh_failed");
    });

    it("does not hard reload after backend recovery on successful POST requests", async () => {
        const reloadSpy = vi.fn();
        Object.defineProperty(window, "location", {
            configurable: true,
            value: {
                ...window.location,
                reload: reloadSpy,
            },
        });

        const rejectedHandler = (api.interceptors.response as any).handlers[0].rejected as (error: unknown) => Promise<unknown>;
        const fulfilledHandler = (api.interceptors.response as any).handlers[0].fulfilled as (response: unknown) => unknown;

        await expect(rejectedHandler({config: {url: "/setup"}, code: "ERR_NETWORK"})).rejects.toMatchObject({
            code: "ERR_NETWORK",
        });

        const response = {
            config: {
                method: "post",
                url: "/setup",
            },
            data: {ok: true},
        };

        expect(fulfilledHandler(response)).toBe(response);
        expect(reloadSpy).not.toHaveBeenCalled();
        expect(sessionStorage.getItem("reloadedAfterBackendRestore")).toBeNull();
    });

    it("reloads after backend recovery on successful GET requests", async () => {
        const reloadSpy = vi.fn();
        Object.defineProperty(window, "location", {
            configurable: true,
            value: {
                ...window.location,
                reload: reloadSpy,
            },
        });

        const rejectedHandler = (api.interceptors.response as any).handlers[0].rejected as (error: unknown) => Promise<unknown>;
        const fulfilledHandler = (api.interceptors.response as any).handlers[0].fulfilled as (response: unknown) => unknown;

        await expect(rejectedHandler({config: {url: "/setup/status"}, code: "ERR_NETWORK"})).rejects.toMatchObject({
            code: "ERR_NETWORK",
        });

        const response = {
            config: {
                method: "get",
                url: "/setup/status",
            },
            data: {is_initialized: false},
        };

        expect(fulfilledHandler(response)).toBe(response);
        expect(reloadSpy).toHaveBeenCalledTimes(1);
        expect(sessionStorage.getItem("reloadedAfterBackendRestore")).toBe("1");
    });
});

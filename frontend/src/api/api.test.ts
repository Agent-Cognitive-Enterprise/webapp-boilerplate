import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../auth/sessionEvents.ts", () => ({
    notifySessionInvalidated: vi.fn(),
}));

vi.mock("../auth/tokenStore.ts", () => ({
    clearAccessToken: vi.fn(),
    getAccessToken: vi.fn(),
    setAccessToken: vi.fn(),
}));

import api from "./api";
import { notifySessionInvalidated } from "../auth/sessionEvents.ts";
import { clearAccessToken } from "../auth/tokenStore.ts";

describe("api interceptor", () => {
    beforeEach(() => {
        vi.clearAllMocks();
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

        expect(clearAccessToken).toHaveBeenCalledTimes(1);
        expect(notifySessionInvalidated).toHaveBeenCalledWith("refresh_failed");
    });
});

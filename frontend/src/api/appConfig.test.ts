import {beforeEach, describe, expect, it, vi} from "vitest";
import api from "./api";
import {fetchAppName, fetchPublicBranding, initializeDocumentTitle} from "./appConfig";

vi.mock("./api", () => ({
    default: {
        get: vi.fn(),
    },
}));

describe("appConfig", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        document.title = "Initial";
    });

    it("fetchAppName returns backend app_name when present", async () => {
        vi.mocked(api.get).mockResolvedValue({
            data: {app_name: "ACE-Labs-Prod"},
        } as any);

        await expect(fetchAppName()).resolves.toBe("ACE-Labs-Prod");
    });

    it("fetchAppName falls back when app_name is missing", async () => {
        vi.mocked(api.get).mockResolvedValue({
            data: {},
        } as any);

        await expect(fetchAppName()).resolves.toBe("webapp-boilerplate");
    });

    it("initializeDocumentTitle sets title from backend", async () => {
        vi.mocked(api.get).mockResolvedValue({
            data: {app_name: "ACE-Labs-Stage"},
        } as any);

        await initializeDocumentTitle();

        expect(document.title).toBe("ACE-Labs-Stage");
    });

    it("initializeDocumentTitle sets fallback on request failure", async () => {
        vi.mocked(api.get).mockRejectedValue(new Error("network"));

        await initializeDocumentTitle();

        expect(document.title).toBe("webapp-boilerplate");
    });

    it("fetchPublicBranding returns branding values from health response", async () => {
        vi.mocked(api.get).mockResolvedValue({
            data: {
                app_name: "ACE Brand",
                site_logo: "data:image/png;base64,abc",
                background_image: "data:image/png;base64,def",
            },
        } as any);

        await expect(fetchPublicBranding()).resolves.toEqual({
            appName: "ACE Brand",
            siteLogo: "data:image/png;base64,abc",
            backgroundImage: "data:image/png;base64,def",
        });
    });
});

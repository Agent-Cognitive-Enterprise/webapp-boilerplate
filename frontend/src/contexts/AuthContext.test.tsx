import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import React from "react";

import { AuthContext, AuthProvider } from "./AuthContext.tsx";
import { notifySessionInvalidated } from "../auth/sessionEvents.ts";
import { fetchUserProfile, loginUser, logoutUser, registerUser } from "../api/auth.ts";
import { getSavedUiLocalePreference } from "../api/userSettings.ts";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
    return {
        ...actual,
        useNavigate: () => mockNavigate,
    };
});

vi.mock("../api/auth.ts", () => ({
    loginUser: vi.fn(),
    fetchUserProfile: vi.fn(),
    registerUser: vi.fn(),
    logoutUser: vi.fn(),
}));

vi.mock("../api/userSettings.ts", async () => {
    const actual = await vi.importActual<typeof import("../api/userSettings.ts")>("../api/userSettings.ts");
    return {
        ...actual,
        getSavedUiLocalePreference: vi.fn(),
    };
});

function ContextHarness() {
    const auth = React.useContext(AuthContext);
    const [loginError, setLoginError] = React.useState<string | null>(null);
    if (!auth) {
        throw new Error("AuthContext not available");
    }

    return (
        <div>
            <div data-testid="token">{auth.token ?? "none"}</div>
            <div data-testid="user-email">{auth.user?.email ?? "none"}</div>
            <div data-testid="login-error">{loginError ?? "none"}</div>
            <button
                type="button"
                onClick={() => {
                    setLoginError(null);
                    void auth.login("user@example.com", "SecurePass123!").catch((error: Error) => {
                        setLoginError(error.message);
                    });
                }}
            >
                Login
            </button>
            <button
                type="button"
                onClick={() => {
                    setLoginError(null);
                    void auth.register("user@example.com", "user@example.com", "SecurePass123!").catch((error: Error) => {
                        setLoginError(error.message);
                    });
                }}
            >
                Register
            </button>
            <button type="button" onClick={() => void auth.logout()}>
                Logout
            </button>
        </div>
    );
}

describe("AuthProvider", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.removeItem("uiLocale");
        mockNavigate.mockReset();
        vi.spyOn(console, "error").mockImplementation(() => undefined);
        vi.mocked(getSavedUiLocalePreference).mockResolvedValue(null);
        vi.mocked(fetchUserProfile).mockRejectedValue(new Error("Unauthorized"));
    });

    function renderProvider() {
        return render(
            <BrowserRouter>
                <AuthProvider>
                    <ContextHarness />
                </AuthProvider>
            </BrowserRouter>
        );
    }

    it("marks the session authenticated on login and loads the user profile", async () => {
        vi.mocked(loginUser).mockResolvedValue({
            access_token: "token-123",
            token_type: "bearer",
        });
        vi.mocked(fetchUserProfile)
            .mockRejectedValueOnce(new Error("Unauthorized"))
            .mockResolvedValueOnce({
                id: "user-1",
                full_name: "Test User",
                email: "user@example.com",
                is_admin: false,
                is_active: true,
            });

        renderProvider();
        fireEvent.click(screen.getByRole("button", { name: "Login" }));

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("cookie-session"));
        expect(screen.getByTestId("user-email")).toHaveTextContent("user@example.com");
        expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
    });

    it("hydrates saved locale preference before completing login", async () => {
        vi.mocked(loginUser).mockResolvedValue({
            access_token: "token-123",
            token_type: "bearer",
        });
        vi.mocked(fetchUserProfile)
            .mockRejectedValueOnce(new Error("Unauthorized"))
            .mockResolvedValueOnce({
                id: "user-1",
                full_name: "Test User",
                email: "user@example.com",
                is_admin: false,
                is_active: true,
            });
        vi.mocked(getSavedUiLocalePreference).mockResolvedValue("ar");

        renderProvider();
        fireEvent.click(screen.getByRole("button", { name: "Login" }));

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("cookie-session"));
        expect(localStorage.getItem("uiLocale")).toBe("ar");
        expect(document.documentElement.lang).toBe("ar");
        expect(document.documentElement.dir).toBe("rtl");
    });

    it("clears local auth state and redirects even when backend logout fails", async () => {
        vi.mocked(fetchUserProfile).mockResolvedValueOnce({
            id: "user-1",
            full_name: "Test User",
            email: "user@example.com",
            is_admin: false,
            is_active: true,
        });
        vi.mocked(logoutUser).mockRejectedValue(new Error("backend down"));

        renderProvider();

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("cookie-session"));
        fireEvent.click(screen.getByRole("button", { name: "Logout" }));

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("none"));
        expect(screen.getByTestId("user-email")).toHaveTextContent("none");
        expect(mockNavigate).toHaveBeenCalledWith("/login");
    });

    it("surfaces a dedicated message for unverified-email login failures", async () => {
        vi.mocked(loginUser).mockRejectedValue({
            response: {
                status: 403,
                data: { detail: "Email verification required" },
            },
        });

        renderProvider();
        fireEvent.click(screen.getByRole("button", { name: "Login" }));

        await waitFor(() =>
            expect(screen.getByTestId("login-error")).toHaveTextContent(
                "Email verification required. Please check your inbox."
            )
        );
        expect(mockNavigate).not.toHaveBeenCalledWith("/dashboard");
    });

    it("surfaces backend duplicate-email errors during registration", async () => {
        vi.mocked(registerUser).mockRejectedValue({
            response: {
                status: 400,
                data: { detail: "Email already registered." },
            },
        });

        renderProvider();
        fireEvent.click(screen.getByRole("button", { name: "Register" }));

        await waitFor(() =>
            expect(screen.getByTestId("login-error")).toHaveTextContent("Email already registered.")
        );
        expect(mockNavigate).not.toHaveBeenCalledWith("/login");
    });

    it("responds to shared session invalidation by clearing auth state and redirecting", async () => {
        vi.mocked(fetchUserProfile).mockResolvedValueOnce({
            id: "user-1",
            full_name: "Test User",
            email: "user@example.com",
            is_admin: false,
            is_active: true,
        });

        renderProvider();

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("cookie-session"));

        notifySessionInvalidated("refresh_failed");

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("none"));
        expect(screen.getByTestId("user-email")).toHaveTextContent("none");
        expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
});

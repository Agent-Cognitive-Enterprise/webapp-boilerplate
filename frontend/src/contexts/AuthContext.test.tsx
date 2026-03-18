import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import React from "react";

import { AuthContext, AuthProvider } from "./AuthContext.tsx";
import { notifySessionInvalidated } from "../auth/sessionEvents.ts";
import { clearAccessToken, getAccessToken } from "../auth/tokenStore.ts";
import { fetchUserProfile, loginUser, logoutUser } from "../api/auth.ts";

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
            <button type="button" onClick={() => void auth.logout()}>
                Logout
            </button>
        </div>
    );
}

describe("AuthProvider", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        clearAccessToken();
        mockNavigate.mockReset();
        vi.spyOn(console, "error").mockImplementation(() => undefined);
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

    it("stores the access token on login and loads the user profile", async () => {
        vi.mocked(loginUser).mockResolvedValue({
            access_token: "token-123",
            token_type: "bearer",
        });
        vi.mocked(fetchUserProfile).mockResolvedValue({
            id: "user-1",
            full_name: "Test User",
            email: "user@example.com",
            is_admin: false,
            is_active: true,
        });

        renderProvider();
        fireEvent.click(screen.getByRole("button", { name: "Login" }));

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("token-123"));
        expect(screen.getByTestId("user-email")).toHaveTextContent("user@example.com");
        expect(getAccessToken()).toBe("token-123");
        expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
    });

    it("clears local auth state and redirects even when backend logout fails", async () => {
        vi.mocked(fetchUserProfile).mockResolvedValue({
            id: "user-1",
            full_name: "Test User",
            email: "user@example.com",
            is_admin: false,
            is_active: true,
        });
        vi.mocked(logoutUser).mockRejectedValue(new Error("backend down"));
        localStorage.setItem("token", "persisted-token");

        renderProvider();

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("persisted-token"));
        fireEvent.click(screen.getByRole("button", { name: "Logout" }));

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("none"));
        expect(screen.getByTestId("user-email")).toHaveTextContent("none");
        expect(getAccessToken()).toBeNull();
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

    it("responds to shared session invalidation by clearing auth state and redirecting", async () => {
        vi.mocked(fetchUserProfile).mockResolvedValue({
            id: "user-1",
            full_name: "Test User",
            email: "user@example.com",
            is_admin: false,
            is_active: true,
        });
        localStorage.setItem("token", "persisted-token");

        renderProvider();

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("persisted-token"));

        notifySessionInvalidated("refresh_failed");

        await waitFor(() => expect(screen.getByTestId("token")).toHaveTextContent("none"));
        expect(screen.getByTestId("user-email")).toHaveTextContent("none");
        expect(getAccessToken()).toBeNull();
        expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
});

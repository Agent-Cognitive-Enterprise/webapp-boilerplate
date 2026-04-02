import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AuthContext } from "../contexts/AuthContext";
import RequireAdmin from "./RequireAdmin";

function renderWithAuth(token: string | null, isAdmin: boolean | null) {
    const authValue = {
        token,
        user: isAdmin === null ? null : { is_admin: isAdmin },
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        setToken: vi.fn(),
    };

    return render(
        <AuthContext.Provider value={authValue as any}>
            <MemoryRouter initialEntries={["/admin"]}>
                <Routes>
                    <Route
                        path="/admin"
                        element={(
                            <RequireAdmin>
                                <div>Admin Content</div>
                            </RequireAdmin>
                        )}
                    />
                    <Route path="/login" element={<div>Login Page</div>} />
                    <Route path="/dashboard" element={<div>Dashboard Page</div>} />
                </Routes>
            </MemoryRouter>
        </AuthContext.Provider>
    );
}

describe("RequireAdmin", () => {
    it("redirects unauthenticated users to login", () => {
        renderWithAuth(null, null);
        expect(screen.getByText("Login Page")).toBeInTheDocument();
        expect(screen.queryByText("Admin Content")).not.toBeInTheDocument();
    });

    it("redirects non-admin users to dashboard", () => {
        renderWithAuth("token-123", false);
        expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
        expect(screen.queryByText("Admin Content")).not.toBeInTheDocument();
    });

    it("renders protected content for admin users", () => {
        renderWithAuth("token-123", true);
        expect(screen.getByText("Admin Content")).toBeInTheDocument();
        expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
        expect(screen.queryByText("Dashboard Page")).not.toBeInTheDocument();
    });
});

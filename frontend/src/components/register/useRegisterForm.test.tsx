import {act, renderHook} from "@testing-library/react";
import React from "react";
import {beforeEach, describe, expect, it, vi} from "vitest";
import {AuthContext} from "../../contexts/AuthContext.tsx";
import {useRegisterForm} from "./useRegisterForm";

vi.mock("../../hooks/useT.ts", () => ({
    useT: (key: string) => key,
}));

function buildWrapper(registerImpl: ReturnType<typeof vi.fn>) {
    return function Wrapper({children}: {children: React.ReactNode}) {
        return (
            <AuthContext.Provider
                value={{
                    token: null,
                    user: null,
                    login: vi.fn(),
                    register: registerImpl,
                    logout: vi.fn(),
                    setToken: vi.fn(),
                }}
            >
                {children}
            </AuthContext.Provider>
        );
    };
}

describe("useRegisterForm", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("submits the current form values through auth context", async () => {
        const register = vi.fn().mockResolvedValue(undefined);
        const {result} = renderHook(() => useRegisterForm(), {
            wrapper: buildWrapper(register),
        });

        act(() => {
            result.current.handleChange({
                target: {name: "full_name", value: "Test User"},
            } as React.ChangeEvent<HTMLInputElement>);
            result.current.handleChange({
                target: {name: "email", value: "test@example.com"},
            } as React.ChangeEvent<HTMLInputElement>);
            result.current.handleChange({
                target: {name: "password", value: "SecurePass123!"},
            } as React.ChangeEvent<HTMLInputElement>);
        });

        await act(async () => {
            await result.current.handleSubmit({
                preventDefault: vi.fn(),
            } as unknown as React.FormEvent<HTMLFormElement>);
        });

        expect(register).toHaveBeenCalledWith("Test User", "test@example.com", "SecurePass123!");
    });

    it("stores and clears submit errors", async () => {
        const register = vi.fn().mockRejectedValueOnce(new Error("Email already registered."));
        const {result} = renderHook(() => useRegisterForm(), {
            wrapper: buildWrapper(register),
        });

        await act(async () => {
            await result.current.handleSubmit({
                preventDefault: vi.fn(),
            } as unknown as React.FormEvent<HTMLFormElement>);
        });

        expect(result.current.error).toBe("Email already registered.");

        act(() => {
            result.current.handleChange({
                target: {name: "email", value: "next@example.com"},
            } as React.ChangeEvent<HTMLInputElement>);
        });

        expect(result.current.error).toBeNull();
    });
});

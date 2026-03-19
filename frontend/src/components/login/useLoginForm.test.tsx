import {act, renderHook} from "@testing-library/react";
import React from "react";
import {beforeEach, describe, expect, it, vi} from "vitest";
import {AuthContext} from "../../contexts/AuthContext.tsx";
import {useLoginForm} from "./useLoginForm";

vi.mock("../../hooks/useT.ts", () => ({
    useT: (key: string) => key,
}));

function buildWrapper(loginImpl: ReturnType<typeof vi.fn>) {
    return function Wrapper({children}: {children: React.ReactNode}) {
        return (
            <AuthContext.Provider
                value={{
                    token: null,
                    user: null,
                    login: loginImpl,
                    register: vi.fn(),
                    logout: vi.fn(),
                    setToken: vi.fn(),
                }}
            >
                {children}
            </AuthContext.Provider>
        );
    };
}

describe("useLoginForm", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.spyOn(console, "error").mockImplementation(() => {});
    });

    it("submits the current credentials through auth context", async () => {
        const login = vi.fn().mockResolvedValue(undefined);
        const {result} = renderHook(() => useLoginForm(), {
            wrapper: buildWrapper(login),
        });

        act(() => {
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

        expect(login).toHaveBeenCalledWith("test@example.com", "SecurePass123!");
        expect(result.current.isLoading).toBe(false);
    });

    it("stores and clears login errors", async () => {
        const login = vi.fn().mockRejectedValueOnce(new Error("Invalid email or password"));
        const {result} = renderHook(() => useLoginForm(), {
            wrapper: buildWrapper(login),
        });

        await act(async () => {
            await result.current.handleSubmit({
                preventDefault: vi.fn(),
            } as unknown as React.FormEvent<HTMLFormElement>);
        });

        expect(result.current.error).toBe("Invalid email or password");

        act(() => {
            result.current.handleChange({
                target: {name: "email", value: "next@example.com"},
            } as React.ChangeEvent<HTMLInputElement>);
        });

        expect(result.current.error).toBeNull();
    });
});

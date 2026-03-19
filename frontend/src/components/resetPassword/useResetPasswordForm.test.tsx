import {act, renderHook} from "@testing-library/react";
import {beforeEach, describe, expect, it, vi} from "vitest";
import api from "../../api/api";
import {useResetPasswordForm} from "./useResetPasswordForm";

vi.mock("../../api/api");
vi.mock("../../hooks/useT.ts", () => ({
    useT: (key: string) => key,
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual("react-router-dom");
    return {
        ...actual,
        useNavigate: () => mockNavigate,
    };
});

describe("useResetPasswordForm", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("submits matching passwords and navigates on success", async () => {
        vi.mocked(api.post).mockResolvedValue({data: {}} as never);
        const {result} = renderHook(() => useResetPasswordForm({token: "test-token-123"}));

        act(() => {
            result.current.setPassword("NewSecure@Pass123");
            result.current.setConfirmPassword("NewSecure@Pass123");
        });

        await act(async () => {
            await result.current.handleSubmit({
                preventDefault: vi.fn(),
            } as unknown as React.FormEvent<HTMLFormElement>);
        });

        expect(api.post).toHaveBeenCalledWith("/auth/reset-password", {
            token: "test-token-123",
            new_password: "NewSecure@Pass123",
        });
        expect(mockNavigate).toHaveBeenCalledWith("/login?reset=success");
    });

    it("stores mismatch errors without calling the api", async () => {
        const {result} = renderHook(() => useResetPasswordForm({token: "test-token-123"}));

        act(() => {
            result.current.setPassword("Password123!");
            result.current.setConfirmPassword("DifferentPass123!");
        });

        await act(async () => {
            await result.current.handleSubmit({
                preventDefault: vi.fn(),
            } as unknown as React.FormEvent<HTMLFormElement>);
        });

        expect(result.current.error).toBe("Passwords do not match");
        expect(api.post).not.toHaveBeenCalled();
    });
});

import {act, renderHook} from "@testing-library/react";
import {beforeEach, describe, expect, it, vi} from "vitest";
import api from "../../api/api";
import {useForgotPasswordForm} from "./useForgotPasswordForm";

vi.mock("../../api/api");

describe("useForgotPasswordForm", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("submits the current email and marks success", async () => {
        vi.mocked(api.post).mockResolvedValue({data: {}} as never);
        const {result} = renderHook(() => useForgotPasswordForm());

        act(() => {
            result.current.setEmail("test@example.com");
        });

        await act(async () => {
            await result.current.handleSubmit({
                preventDefault: vi.fn(),
            } as unknown as React.FormEvent<HTMLFormElement>);
        });

        expect(api.post).toHaveBeenCalledWith("/auth/forgot-password", {
            email: "test@example.com",
        });
        expect(result.current.success).toBe(true);
        expect(result.current.isLoading).toBe(false);
    });

    it("treats 404 as success and hides backend details", async () => {
        vi.mocked(api.post).mockRejectedValue({
            response: {status: 404, data: {detail: "Not Found"}},
        });
        const {result} = renderHook(() => useForgotPasswordForm());

        await act(async () => {
            await result.current.handleSubmit({
                preventDefault: vi.fn(),
            } as unknown as React.FormEvent<HTMLFormElement>);
        });

        expect(result.current.success).toBe(true);
        expect(result.current.error).toBeNull();
    });
});

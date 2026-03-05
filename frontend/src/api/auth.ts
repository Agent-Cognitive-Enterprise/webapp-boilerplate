// /frontend/src/api/auth.ts

import api from "./api";
import type {
    LoginCredentials,
    LoginResponse,
    UserProfile,
    RegisterPayload,
    ExtendedAxiosRequestConfig
} from "./types";

function isLoginResponse(data: unknown): data is LoginResponse {
    return typeof data === "object" && data !== null &&
        typeof (data as any).access_token === "string" &&
        typeof (data as any).token_type === "string";
}

export const loginUser = async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const params = new URLSearchParams(Object.entries(credentials));
    const response = await api.post("/auth/token", params, {
        headers: {"Content-Type": "application/x-www-form-urlencoded"},
        skipAuthRefresh: true,  // Don't try to refresh on login failure
    } as ExtendedAxiosRequestConfig);
    if (!isLoginResponse(response.data)) throw new Error("Invalid login response");
    // Don't set token here - let AuthContext handle it
    return response.data;
};

export async function fetchUserProfile(): Promise<UserProfile> {
    const resp = await api.get("/users/me/");
    const raw = resp.data;
    const resolvedIsAdmin =
        typeof raw?.is_admin === "boolean"
            ? raw.is_admin
            : typeof raw?.is_superuser === "boolean"
                ? raw.is_superuser
                : undefined;

    if (typeof resp.data?.full_name !== "string" ||
        typeof resp.data?.email !== "string" ||
        typeof resp.data?.id !== "string" ||
        typeof resolvedIsAdmin !== "boolean" ||
        typeof resp.data?.is_active !== "boolean")
        throw new Error("Invalid user profile");
    return {
        ...raw,
        is_admin: resolvedIsAdmin,
    };
}

export async function registerUser(payload: RegisterPayload): Promise<void> {
    await api.post("/auth/register", payload, {
        headers: {"Content-Type": "application/json"},
    });
}

export async function logoutUser(): Promise<void> {
    try {
        // Notify backend to revoke refresh token
        await api.post("/auth/logout");
    } catch (error) {
        // Log error but continue with local logout
        console.error("Backend logout failed:", error);
    } finally {
        // Always clear local storage
        localStorage.removeItem("token");
    }
}

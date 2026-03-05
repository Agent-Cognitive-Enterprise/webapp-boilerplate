// /frontend/src/api/types.ts
import type {InternalAxiosRequestConfig} from "axios";

// Extended config for refresh flow
export interface ExtendedAxiosRequestConfig extends InternalAxiosRequestConfig {
    _retry?: boolean;
    skipAuthRefresh?: boolean; // skip 401 refresh
    skipAuthHeader?: boolean;  // skip attaching Authorisation
}

export interface LoginCredentials {
    username: string;
    password: string;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
}

export interface UserProfile {
    id: string;
    full_name: string;
    email: string;
    is_admin: boolean;
    is_superuser?: boolean;
    is_active: boolean;
    email_verified?: boolean;
}

export interface RegisterPayload {
    full_name: string;
    email: string;
    password: string;
}

export interface RefreshResponse {
    access_token: string;
}

export interface Opus {
    user_id: string;
    id: string;
    title: string;
    description?: string;
    status?: string;
    created_at: string;
    updated_at: string;
    deleted_at?: string | null;
}

export interface Chapter {
    id: string;
    opus_id: string;
    title: string;
    position: number;
    created_at: string;
    updated_at: string;
    deleted_at?: string | null;
}

export interface ManagedUser {
    id: string;
    full_name: string;
    email: string;
    is_active: boolean;
    is_admin: boolean;
    email_verified: boolean;
    created_at: string;
}

export type NewManagedUser = {
    full_name: string;
    email: string;
    password: string;
    is_admin: boolean;
};

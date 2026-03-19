import {type FormEvent, useEffect, useState} from "react";
import api from "../../api/api.ts";
import type {ManagedUser, NewManagedUser} from "./types";

const EMPTY_NEW_USER: NewManagedUser = {
    full_name: "",
    email: "",
    password: "",
    is_admin: false,
};

export function useUserManagement(authToken: string | null, isAdmin: boolean) {
    const canUseMatchMedia = typeof window !== "undefined" && typeof window.matchMedia === "function";
    const [users, setUsers] = useState<ManagedUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [errorKey, setErrorKey] = useState<string | null>(null);
    const [tableMessageKey, setTableMessageKey] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);
    const [isLargeScreen, setIsLargeScreen] = useState(() => (
        canUseMatchMedia ? window.matchMedia("(min-width: 1024px)").matches : true
    ));
    const [newUser, setNewUser] = useState<NewManagedUser>(EMPTY_NEW_USER);

    useEffect(() => {
        if (!isAdmin || !authToken) {
            setLoading(false);
            setUsers([]);
            return;
        }

        const fetchUsers = async () => {
            try {
                setLoading(true);
                const response = await api.get("/users", {
                    headers: {Authorization: `Bearer ${authToken}`},
                });
                setUsers(response.data);
                setErrorKey(null);
                setTableMessageKey(response.data.length === 0 ? "user_management.message.no_users_found" : null);
            } catch (err) {
                console.error("Error fetching users:", err);
                setUsers([]);
                setTableMessageKey("user_management.message.no_users_found");
            } finally {
                setLoading(false);
            }
        };

        fetchUsers();
    }, [authToken, isAdmin]);

    useEffect(() => {
        if (!canUseMatchMedia) {
            return;
        }

        const mediaQuery = window.matchMedia("(min-width: 1024px)");
        const handler = (event: MediaQueryListEvent) => setIsLargeScreen(event.matches);
        setIsLargeScreen(mediaQuery.matches);
        mediaQuery.addEventListener("change", handler);
        return () => mediaQuery.removeEventListener("change", handler);
    }, [canUseMatchMedia]);

    const toggleUserActive = async (userId: string, currentStatus: boolean) => {
        try {
            await api.put(
                `/users/${userId}`,
                {is_active: !currentStatus},
                {headers: {Authorization: `Bearer ${authToken}`}},
            );
            setUsers((currentUsers) => currentUsers.map((user) => (
                user.id === userId ? {...user, is_active: !currentStatus} : user
            )));
        } catch (err) {
            console.error("Error updating user:", err);
            setErrorKey("user_management.error.failed_update");
        }
    };

    const createUser = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setErrorKey(null);
        setCreating(true);
        try {
            const response = await api.post("/users", newUser, {
                headers: {Authorization: `Bearer ${authToken}`},
            });
            setUsers((currentUsers) => [response.data, ...currentUsers]);
            setNewUser(EMPTY_NEW_USER);
            setTableMessageKey(null);
        } catch (err) {
            console.error("Error creating user:", err);
            setErrorKey("user_management.error.failed_create");
        } finally {
            setCreating(false);
        }
    };

    const deleteUser = async (userId: string) => {
        setErrorKey(null);
        try {
            await api.delete(`/users/${userId}`, {
                headers: {Authorization: `Bearer ${authToken}`},
            });
            setUsers((currentUsers) => currentUsers.filter((user) => user.id !== userId));
        } catch (err) {
            console.error("Error deleting user:", err);
            setErrorKey("user_management.error.failed_delete");
        }
    };

    return {
        users,
        loading,
        errorKey,
        tableMessageKey,
        creating,
        isLargeScreen,
        newUser,
        setNewUser,
        createUser,
        toggleUserActive,
        deleteUser,
    };
}

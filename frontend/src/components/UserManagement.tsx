// /frontend/src/components/UserManagement.tsx

import { type FormEvent, useContext, useEffect, useState } from "react";
import { AuthContext } from "../contexts/AuthContext.tsx";
import UiLabel from "./UiLabel.tsx";
import api from "../api/api.ts";
import { Navigate } from "react-router-dom";

interface User {
    id: string;
    full_name: string;
    email: string;
    is_active: boolean;
    is_admin: boolean;
    email_verified: boolean;
    created_at: string;
}

export default function UserManagement() {
    const auth = useContext(AuthContext);
    const canUseMatchMedia = typeof window !== "undefined" && typeof window.matchMedia === "function";
    const isAdmin = Boolean(auth?.user?.is_admin);
    const authToken = auth?.token ?? null;
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [errorKey, setErrorKey] = useState<string | null>(null);
    const [tableMessageKey, setTableMessageKey] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);
    const [isLargeScreen, setIsLargeScreen] = useState(() => (
        canUseMatchMedia ? window.matchMedia("(min-width: 1024px)").matches : true
    ));
    const [newUser, setNewUser] = useState({
        full_name: "",
        email: "",
        password: "",
        is_admin: false,
    });

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
                    headers: {
                        Authorization: `Bearer ${authToken}`,
                    },
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
                { is_active: !currentStatus },
                {
                    headers: {
                        Authorization: `Bearer ${authToken}`,
                    },
                }
            );
            // Refresh user list
            setUsers(users.map(u =>
                u.id === userId ? { ...u, is_active: !currentStatus } : u
            ));
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
            const response = await api.post(
                "/users",
                newUser,
                {
                    headers: {
                        Authorization: `Bearer ${authToken}`,
                    },
                },
            );
            setUsers([response.data, ...users]);
            setNewUser({full_name: "", email: "", password: "", is_admin: false});
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
                headers: {
                    Authorization: `Bearer ${authToken}`,
                },
            });
            setUsers(users.filter((u) => u.id !== userId));
        } catch (err) {
            console.error("Error deleting user:", err);
            setErrorKey("user_management.error.failed_delete");
        }
    };

    function formatDate(isoDate: string): string {
        return new Date(isoDate).toLocaleDateString();
    }

    // Only admins can access this page
    if (!isAdmin) {
        return <Navigate to="/dashboard" replace />;
    }

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <div className="ace-card ace-card-strong ace-card-pad max-w-6xl">
                <h1 className="mb-6 text-2xl font-bold text-slate-800 sm:text-3xl">
                    <UiLabel k="user_management.title.user_management" />
                </h1>

                {errorKey && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        <UiLabel k={errorKey} />
                    </div>
                )}

                {loading ? (
                    <div className="text-center py-8">
                        <UiLabel k="user_management.message.loading" />...
                    </div>
                ) : (
                    <div className="space-y-6">
                        <form onSubmit={createUser} className="rounded border border-gray-200 p-4 bg-gray-50">
                            <h2 className="text-lg font-semibold text-gray-800 mb-3">
                                <UiLabel k="user_management.title.create_user" />
                            </h2>
                            <div className="grid grid-cols-1 gap-3 lg:grid-cols-4">
                                <label className="block">
                                    <span className="text-xs text-gray-600"><UiLabel k="user_management.field.full_name" /></span>
                                    <input className="ace-input" aria-label="user_management.field.full_name" value={newUser.full_name} onChange={(e) => setNewUser({...newUser, full_name: e.target.value})} required />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-gray-600"><UiLabel k="user_management.table.email" /></span>
                                    <input className="ace-input" aria-label="user_management.field.email" type="email" value={newUser.email} onChange={(e) => setNewUser({...newUser, email: e.target.value})} required />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-gray-600"><UiLabel k="user_management.field.password" /></span>
                                    <input className="ace-input" aria-label="user_management.field.password" type="password" value={newUser.password} onChange={(e) => setNewUser({...newUser, password: e.target.value})} required minLength={8} />
                                </label>
                                <label className="flex items-center gap-2 text-sm">
                                    <input type="checkbox" checked={newUser.is_admin} onChange={(e) => setNewUser({...newUser, is_admin: e.target.checked})} />
                                    <UiLabel k="user_management.field.admin_user" />
                                </label>
                            </div>
                            <button disabled={creating} className="mt-3 rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400">
                                {creating ? <UiLabel k="user_management.button.creating" /> : <UiLabel k="user_management.button.create_user" />}
                            </button>
                        </form>

                        {isLargeScreen && (
                        <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <UiLabel k="user_management.table.email" />
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <UiLabel k="user_management.table.status" />
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <UiLabel k="user_management.table.role" />
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <UiLabel k="user_management.table.created_at" />
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <UiLabel k="user_management.table.email_verified" />
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        <UiLabel k="user_management.table.actions" />
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {users.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-8 text-center text-sm text-gray-500">
                                            {tableMessageKey ? <UiLabel k={tableMessageKey} /> : <UiLabel k="user_management.message.no_users_found" />}
                                        </td>
                                    </tr>
                                )}
                                {users.map((user) => (
                                    <tr key={user.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {user.email}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                                user.is_active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-red-100 text-red-800'
                                            }`}>
                                                {user.is_active ? (
                                                    <UiLabel k="user_management.status.active" />
                                                ) : (
                                                    <UiLabel k="user_management.status.inactive" />
                                                )}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {user.is_admin ? (
                                                <UiLabel k="user_management.role.admin" />
                                            ) : (
                                                <UiLabel k="user_management.role.user" />
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatDate(user.created_at)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {user.email_verified ? <UiLabel k="user_management.status.yes" /> : <UiLabel k="user_management.status.no" />}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            <div className="flex gap-3">
                                                <button
                                                    onClick={() => toggleUserActive(user.id, user.is_active)}
                                                    className={`${
                                                        user.is_active
                                                            ? 'text-red-600 hover:text-red-900'
                                                            : 'text-green-600 hover:text-green-900'
                                                    }`}
                                                >
                                                    {user.is_active ? (
                                                        <UiLabel k="user_management.action.deactivate" />
                                                    ) : (
                                                        <UiLabel k="user_management.action.activate" />
                                                    )}
                                                </button>
                                                <button
                                                    onClick={() => deleteUser(user.id)}
                                                    className="text-red-700 hover:text-red-900"
                                                >
                                                    <UiLabel k="user_management.action.delete" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        </div>
                        )}
                        {!isLargeScreen && (
                        <div className="grid grid-cols-1 gap-3">
                            {users.length === 0 && (
                                <div className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-600">
                                    {tableMessageKey ? <UiLabel k={tableMessageKey} /> : <UiLabel k="user_management.message.no_users_found" />}
                                </div>
                            )}
                            {users.map((user) => (
                                <article key={user.id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                                    <p className="text-sm font-semibold text-slate-900">{user.email}</p>
                                    <p className="mt-1 text-xs text-slate-600">
                                        <UiLabel k="user_management.table.created_at" />: {formatDate(user.created_at)}
                                    </p>
                                    <div className="mt-2 flex flex-wrap gap-2 text-xs">
                                        <span className={`rounded-full px-2 py-1 ${user.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                                            {user.is_active ? <UiLabel k="user_management.status.active" /> : <UiLabel k="user_management.status.inactive" />}
                                        </span>
                                        <span className="rounded-full bg-blue-100 px-2 py-1 text-blue-800">
                                            {user.is_admin ? <UiLabel k="user_management.role.admin" /> : <UiLabel k="user_management.role.user" />}
                                        </span>
                                        <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-700">
                                            <UiLabel k="user_management.table.email_verified" />: {user.email_verified ? <UiLabel k="user_management.status.yes" /> : <UiLabel k="user_management.status.no" />}
                                        </span>
                                    </div>
                                    <div className="mt-3 flex flex-wrap gap-3 text-sm font-medium">
                                        <button
                                            onClick={() => toggleUserActive(user.id, user.is_active)}
                                            className={user.is_active ? "text-red-700" : "text-green-700"}
                                        >
                                            {user.is_active ? <UiLabel k="user_management.action.deactivate" /> : <UiLabel k="user_management.action.activate" />}
                                        </button>
                                        <button onClick={() => deleteUser(user.id)} className="text-red-700">
                                            <UiLabel k="user_management.action.delete" />
                                        </button>
                                    </div>
                                </article>
                            ))}
                        </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

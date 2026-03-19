// /frontend/src/components/UserManagement.tsx

import {useContext} from "react";
import { AuthContext } from "../contexts/AuthContext.tsx";
import UiLabel from "./UiLabel.tsx";
import { Navigate } from "react-router-dom";
import {useUserManagement} from "./userManagement/useUserManagement.ts";
import {UserManagementList} from "./userManagement/UserManagementList.tsx";

export default function UserManagement() {
    const auth = useContext(AuthContext);
    const isAdmin = Boolean(auth?.user?.is_admin);
    const authToken = auth?.token ?? null;
    const {
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
    } = useUserManagement(authToken, isAdmin);

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

                        <UserManagementList
                            users={users}
                            isLargeScreen={isLargeScreen}
                            tableMessageKey={tableMessageKey}
                            onToggleActive={toggleUserActive}
                            onDeleteUser={deleteUser}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}

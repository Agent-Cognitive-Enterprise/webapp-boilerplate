import UiLabel from "../UiLabel.tsx";
import type {ManagedUser} from "./types";

type UserManagementListProps = {
    users: ManagedUser[];
    isLargeScreen: boolean;
    tableMessageKey: string | null;
    onToggleActive: (userId: string, currentStatus: boolean) => void;
    onDeleteUser: (userId: string) => void;
};

function formatDate(isoDate: string): string {
    return new Date(isoDate).toLocaleDateString();
}

export function UserManagementList({
    users,
    isLargeScreen,
    tableMessageKey,
    onToggleActive,
    onDeleteUser,
}: UserManagementListProps) {
    if (isLargeScreen) {
        return (
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                <UiLabel k="user_management.table.email" />
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                <UiLabel k="user_management.table.status" />
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                <UiLabel k="user_management.table.role" />
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                <UiLabel k="user_management.table.created_at" />
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                <UiLabel k="user_management.table.email_verified" />
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                <UiLabel k="user_management.table.actions" />
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                        {users.length === 0 && (
                            <tr>
                                <td colSpan={6} className="px-6 py-8 text-center text-sm text-gray-500">
                                    {tableMessageKey ? <UiLabel k={tableMessageKey} /> : <UiLabel k="user_management.message.no_users_found" />}
                                </td>
                            </tr>
                        )}
                        {users.map((user) => (
                            <tr key={user.id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{user.email}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span
                                        className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${
                                            user.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                                        }`}
                                    >
                                        {user.is_active ? <UiLabel k="user_management.status.active" /> : <UiLabel k="user_management.status.inactive" />}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {user.is_admin ? <UiLabel k="user_management.role.admin" /> : <UiLabel k="user_management.role.user" />}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(user.created_at)}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {user.email_verified ? <UiLabel k="user_management.status.yes" /> : <UiLabel k="user_management.status.no" />}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                    <div className="flex gap-3">
                                        <button
                                            onClick={() => onToggleActive(user.id, user.is_active)}
                                            className={user.is_active ? "text-red-600 hover:text-red-900" : "text-green-600 hover:text-green-900"}
                                        >
                                            {user.is_active ? <UiLabel k="user_management.action.deactivate" /> : <UiLabel k="user_management.action.activate" />}
                                        </button>
                                        <button onClick={() => onDeleteUser(user.id)} className="text-red-700 hover:text-red-900">
                                            <UiLabel k="user_management.action.delete" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }

    return (
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
                        <button onClick={() => onToggleActive(user.id, user.is_active)} className={user.is_active ? "text-red-700" : "text-green-700"}>
                            {user.is_active ? <UiLabel k="user_management.action.deactivate" /> : <UiLabel k="user_management.action.activate" />}
                        </button>
                        <button onClick={() => onDeleteUser(user.id)} className="text-red-700">
                            <UiLabel k="user_management.action.delete" />
                        </button>
                    </div>
                </article>
            ))}
        </div>
    );
}

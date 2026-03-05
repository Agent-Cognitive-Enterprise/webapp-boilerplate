// /frontend/src/components/Dashboard.tsx

import { useContext } from "react";
import { Link } from "react-router-dom";
import { AuthContext } from "../contexts/AuthContext.tsx";
import UiLabel from "./UiLabel.tsx";

export default function Dashboard() {
    const auth = useContext(AuthContext);

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <div className="ace-card ace-card-strong ace-card-pad max-w-4xl">
                <h1 className="mb-6 text-2xl font-bold text-slate-800 sm:text-3xl">
                    <UiLabel k="dashboard.title.welcome" />
                </h1>
                <div className="space-y-4">
                    <p className="text-base text-slate-700 sm:text-lg">
                        <UiLabel k="dashboard.message.logged_in_as" />: <span className="font-semibold">{auth?.user?.email}</span>
                    </p>
                    <div className="border-t pt-4">
                        <h2 className="mb-3 text-lg font-semibold text-slate-800 sm:text-xl">
                            <UiLabel k="dashboard.title.quick_links" />
                        </h2>
                        <ul className="list-disc list-inside space-y-2 text-gray-700">
                            <li>
                                <Link to="/profile" className="text-blue-600 hover:text-blue-800 hover:underline">
                                    <UiLabel k="dashboard.link.view_profile" />
                                </Link>
                            </li>
                            {auth?.user?.is_admin && (
                                <li>
                                    <Link to="/users" className="text-blue-600 hover:text-blue-800 hover:underline">
                                        <UiLabel k="dashboard.link.manage_users" />
                                    </Link>
                                </li>
                            )}
                            {auth?.user?.is_admin && (
                                <li>
                                    <Link to="/admin/settings" className="text-blue-600 hover:text-blue-800 hover:underline">
                                        <UiLabel k="dashboard.link.admin_settings" />
                                    </Link>
                                </li>
                            )}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}

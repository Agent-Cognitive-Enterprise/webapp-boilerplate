import { type JSX, useContext } from "react";
import { Navigate } from "react-router-dom";

import { AuthContext } from "../contexts/AuthContext.tsx";

export default function RequireAdmin({ children }: { children: JSX.Element }) {
    const auth = useContext(AuthContext);

    if (auth?.isLoading) {
        return <div className="min-h-[40vh]" />;
    }

    if (!auth?.token) {
        return <Navigate to="/login" replace />;
    }

    if (!auth.user?.is_admin) {
        return <Navigate to="/dashboard" replace />;
    }

    return children;
}

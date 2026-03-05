import {type JSX, useContext} from "react";
import {AuthContext} from "../contexts/AuthContext";
import {Navigate} from "react-router-dom";

export default function RequireAuth({children}: { children: JSX.Element }) {
    const auth = useContext(AuthContext);
    if (!auth?.token) {
        // Not authenticated, redirect to /login
        return <Navigate to="/login" replace/>;
    }
    return children;
}
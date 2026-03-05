// /frontend/src/hooks/useKeepUserLoggedIn.ts

import {useEffect, useContext} from "react";
import {AuthContext} from "../contexts/AuthContext.tsx";
import {getUserSettings} from "../api/userSettings.ts";
import api from "../api/api.ts";

export function useKeepUserLoggedIn(route = "/profile", intervalMs = 120_000) {
    const auth = useContext(AuthContext);

    useEffect(() => {
        if (!auth?.token) return;

        const timer = setInterval(async () => {
            if (typeof document !== "undefined" && document.visibilityState === "hidden") {
                return;
            }
            try {
                // lightweight call to keep the session alive
                await getUserSettings(route);

            } catch (err) {
                console.warn("Session may have expired, attempting refresh via /auth/refresh...", err);
                try {
                    const res = await api.post("/auth/refresh");
                    auth.setToken(res.data.access_token); // <-- update your AuthContext token
                } catch {
                    // Refresh failed, log out
                    console.log("Refresh failed, logging out");
                    auth.logout();
                }
            }
        }, intervalMs);

        return () => clearInterval(timer);
    }, [auth, route, intervalMs]);
}

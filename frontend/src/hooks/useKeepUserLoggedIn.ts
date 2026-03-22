// /frontend/src/hooks/useKeepUserLoggedIn.ts

import {useEffect, useContext} from "react";
import {AuthContext} from "../contexts/AuthContext.tsx";
import {getUserSettings} from "../api/userSettings.ts";

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
            } catch {
                // The API client handles refresh and session invalidation centrally.
            }
        }, intervalMs);

        return () => clearInterval(timer);
    }, [auth, route, intervalMs]);
}

import {useContext, useEffect, useState} from "react";
import {useLocation} from "react-router-dom";
import {fetchPublicBranding} from "../../api/appConfig.ts";
import backgroundImage from "../../assets/beach-4455224_1920.jpg";
import mobileBackgroundImage from "../../assets/beach-4455224_mobile_720x1280.jpg";
import {AuthContext} from "../../contexts/AuthContext.tsx";

const BRANDING_BG_STORAGE_KEY = "branding.backgroundImage";
const BRANDING_LOGO_STORAGE_KEY = "branding.siteLogo";
const MOBILE_VIEWPORT_QUERY = "(max-width: 767px)";

function readStoredBranding(key: string): string | null {
    const value = localStorage.getItem(key);
    if (!value || value.trim().length === 0) {
        return null;
    }
    return value;
}

function getDefaultBackgroundForViewport(isMobileViewport: boolean): string {
    return isMobileViewport ? mobileBackgroundImage : backgroundImage;
}

function isMobileViewport(): boolean {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
        return false;
    }
    return window.matchMedia(MOBILE_VIEWPORT_QUERY).matches;
}

export function useInitializedAppShellState() {
    const auth = useContext(AuthContext);
    const location = useLocation();
    const [siteLogo, setSiteLogo] = useState<string | null>(() => readStoredBranding(BRANDING_LOGO_STORAGE_KEY));
    const [brandingBackgroundUrl, setBrandingBackgroundUrl] = useState<string | null>(() => readStoredBranding(BRANDING_BG_STORAGE_KEY));
    const [mobileViewport, setMobileViewport] = useState<boolean>(() => isMobileViewport());
    const [mobileNavOpen, setMobileNavOpen] = useState(false);

    useEffect(() => {
        let active = true;

        async function loadBranding() {
            try {
                const branding = await fetchPublicBranding();

                if (!active) {
                    return;
                }

                setSiteLogo(branding.siteLogo);

                if (branding.siteLogo) {
                    localStorage.setItem(BRANDING_LOGO_STORAGE_KEY, branding.siteLogo);
                } else {
                    localStorage.removeItem(BRANDING_LOGO_STORAGE_KEY);
                }

                if (branding.backgroundImage) {
                    setBrandingBackgroundUrl(branding.backgroundImage);
                    localStorage.setItem(BRANDING_BG_STORAGE_KEY, branding.backgroundImage);
                } else {
                    setBrandingBackgroundUrl(null);
                    localStorage.removeItem(BRANDING_BG_STORAGE_KEY);
                }
            } catch {
                if (!active) {
                    return;
                }
            }
        }

        void loadBranding();

        return () => {
            active = false;
        };
    }, []);

    useEffect(() => {
        setMobileNavOpen(false);
    }, [auth?.token, location.pathname]);

    useEffect(() => {
        if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
            return;
        }

        const mediaQuery = window.matchMedia(MOBILE_VIEWPORT_QUERY);
        const onChange = (event: MediaQueryListEvent) => setMobileViewport(event.matches);
        setMobileViewport(mediaQuery.matches);

        if (typeof mediaQuery.addEventListener === "function") {
            mediaQuery.addEventListener("change", onChange);
            return () => mediaQuery.removeEventListener("change", onChange);
        }

        mediaQuery.addListener(onChange);
        return () => mediaQuery.removeListener(onChange);
    }, []);

    return {
        auth,
        siteLogo,
        mobileNavOpen,
        setMobileNavOpen,
        backgroundUrl: brandingBackgroundUrl ?? getDefaultBackgroundForViewport(mobileViewport),
        isAdmin: Boolean(auth?.user?.is_admin),
    };
}

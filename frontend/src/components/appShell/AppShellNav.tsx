import {Link} from "react-router-dom";
import UiLabel from "../UiLabel.tsx";

type AppShellNavProps = {
    hasToken: boolean;
    isAdmin: boolean;
    mobileNavOpen: boolean;
    onToggleMobileNav: () => void;
    onLogout: () => void;
    siteLogo: string | null;
    siteLogoAltText: string;
};

function NavLinks({
    hasToken,
    isAdmin,
    onLogout,
    mobile,
}: {
    hasToken: boolean;
    isAdmin: boolean;
    onLogout: () => void;
    mobile?: boolean;
}) {
    const linkClassName = mobile ? "ace-nav-link w-full justify-center" : "ace-nav-link";
    const buttonClassName = mobile ? "ace-nav-button w-full justify-center" : "ace-nav-button";

    if (!hasToken) {
        return (
            <>
                <li><Link to="/register" className={linkClassName}><UiLabel k="nav.title.register" /></Link></li>
                <li><Link to="/login" className={linkClassName}><UiLabel k="nav.title.login" /></Link></li>
            </>
        );
    }

    return (
        <>
            <li><Link to="/dashboard" className={linkClassName}><UiLabel k="nav.title.dashboard" /></Link></li>
            <li><Link to="/profile" className={linkClassName}><UiLabel k="nav.title.profile" /></Link></li>
            {isAdmin && <li><Link to="/users" className={linkClassName}><UiLabel k="nav.title.users" /></Link></li>}
            {isAdmin && <li><Link to="/admin/settings" className={linkClassName}><UiLabel k="nav.title.admin_settings" /></Link></li>}
            <li>
                <button onClick={onLogout} className={buttonClassName}>
                    <UiLabel k="nav.title.logout" />
                </button>
            </li>
        </>
    );
}

export function AppShellNav({
    hasToken,
    isAdmin,
    mobileNavOpen,
    onToggleMobileNav,
    onLogout,
    siteLogo,
    siteLogoAltText,
}: AppShellNavProps) {
    return (
        <nav className="fixed top-0 left-0 z-50 w-full border-b border-white/20 bg-slate-900/70 shadow backdrop-blur-md">
            <div className="mx-auto max-w-7xl px-4 py-3 md:px-6">
                <div className="flex items-center justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2">
                        {siteLogo && (
                            <img
                                src={siteLogo}
                                alt={siteLogoAltText}
                                className="h-8 w-auto max-w-32 object-contain md:max-w-40"
                            />
                        )}
                    </div>

                    <button
                        type="button"
                        onClick={onToggleMobileNav}
                        className="rounded-md border border-white/30 px-3 py-1.5 text-sm font-semibold text-white md:hidden"
                        aria-expanded={mobileNavOpen}
                        aria-label="Toggle navigation menu"
                    >
                        {mobileNavOpen ? "Close" : "Menu"}
                    </button>

                    <ul className="hidden items-center gap-1 md:flex">
                        <NavLinks hasToken={hasToken} isAdmin={isAdmin} onLogout={onLogout} />
                    </ul>
                </div>

                {mobileNavOpen && (
                    <ul className="mt-3 grid grid-cols-1 gap-2 md:hidden">
                        <NavLinks hasToken={hasToken} isAdmin={isAdmin} onLogout={onLogout} mobile />
                    </ul>
                )}
            </div>
        </nav>
    );
}

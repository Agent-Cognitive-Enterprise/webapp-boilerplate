import type {ReactNode} from "react";

import backgroundImage from "../../assets/beach-4455224_1920.jpg";
import mobileBackgroundImage from "../../assets/beach-4455224_mobile_720x1280.jpg";

type SetupWizardShellProps = {
    children: ReactNode;
};

export function SetupWizardShell({children}: SetupWizardShellProps) {
    return (
        <div data-testid="setup-background-shell" className="relative min-h-screen w-full overflow-hidden bg-slate-950">
            <picture className="pointer-events-none absolute inset-0 block h-full w-full">
                <source media="(max-width: 767px)" srcSet={mobileBackgroundImage} />
                <img
                    src={backgroundImage}
                    alt=""
                    aria-hidden="true"
                    className="h-full w-full object-cover object-center"
                />
            </picture>
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-slate-950/34 via-sky-950/12 to-slate-950/45" />
            <div className="relative z-10 flex min-h-screen w-full flex-col px-3 py-4 sm:px-6 sm:py-8">
                <div data-testid="setup-shell-center" className="mx-auto my-auto flex w-full justify-center">
                    {children}
                </div>
            </div>
        </div>
    );
}

import {Link} from "react-router-dom";
import {useSetupWizardForm} from "./setupWizard/useSetupWizardForm";
import {SetupWizardForm} from "./setupWizard/SetupWizardForm";
import {SetupWizardShell} from "./setupWizard/SetupWizardShell";
import type {SetupEmailDefaults} from "./setupWizard/types";

type SetupWizardProps = {
    isInitialized: boolean;
    onSetupComplete: () => void;
    seedLocales: string[];
    emailDefaults?: SetupEmailDefaults;
};

export default function SetupWizard({isInitialized, onSetupComplete, seedLocales, emailDefaults}: SetupWizardProps) {
    const form = useSetupWizardForm({
        seedLocales,
        emailDefaults: emailDefaults ?? null,
        onSetupComplete,
    });
    const {copy} = form;

    if (isInitialized) {
        return (
            <SetupWizardShell>
                <div
                    data-testid="setup-wizard-card"
                    className="ace-card ace-card-pad w-full max-w-xl border-white/35 bg-white/72 shadow-[0_24px_70px_rgba(15,23,42,0.24)] backdrop-blur-xl"
                >
                    <h1 className="text-2xl font-semibold text-gray-900">{copy.alreadyConfiguredTitle}</h1>
                    <p className="mt-3 text-gray-700">{copy.alreadyConfiguredDescription}</p>
                    <Link
                        className="inline-block mt-6 text-blue-700 hover:text-blue-900 underline"
                        to="/login"
                    >
                        {copy.goToLogin}
                    </Link>
                </div>
            </SetupWizardShell>
        );
    }

    return (
        <SetupWizardShell>
            <SetupWizardForm form={form} />
        </SetupWizardShell>
    );
}

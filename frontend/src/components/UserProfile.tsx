// frontend/src/components/UserProfile.tsx

import {useContext} from 'react';
import {AuthContext} from '../contexts/AuthContext.tsx';
import LocaleSelector from "./UiLocaleSelector.tsx";
import UiLabel from "./UiLabel.tsx";

interface AuthContextType {
    user: {
        full_name: string;
        email: string;
    };
    logout: () => void;
}

const UserProfile = () => {
    const {user, logout} = useContext(AuthContext) as AuthContextType;

    if (!user) {
        return (
            <div>
                <UiLabel k="common.loading"/>
            </div>
        );
    }

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <div className="ace-card ace-card-strong ace-card-pad w-full max-w-md">
                <h2 className="mb-6 text-center text-2xl font-bold text-slate-800 sm:text-3xl">
                    <UiLabel k="profile.title.user_profile"/>
                </h2>

                <label className="block mb-4">
                    <span
                        className="ace-field-label"
                    >
                        <UiLabel k="profile.label.full_name"/>
                    </span>
                    <p
                        className="ace-input"
                    >
                        {user.full_name}
                    </p>
                </label>

                <label className="block mb-6">
                    <span
                        className="ace-field-label"
                    >
                        <UiLabel k="profile.label.email"/>
                    </span>
                    <p
                        className="ace-input"
                    >
                        {user.email}
                    </p>
                </label>

                <label className="block mb-6">
                    <span
                        className="ace-field-label"
                    >
                        <UiLabel k="profile.label.language" />
                    </span>
                    <LocaleSelector/>
                </label>

                <button
                    onClick={logout}
                    className="w-full rounded-md bg-red-500 py-2 font-semibold text-white transition-colors hover:bg-red-600"
                    data-testid="logout-button"
                >
                    <UiLabel k="profile.button.logout"/>
                </button>
            </div>
        </div>
    );
};

export default UserProfile;

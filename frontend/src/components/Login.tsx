// frontend/src/components/Login.tsx

import React, {useState, useContext} from 'react';
import {AuthContext} from '../contexts/AuthContext.tsx';
import UiLabel from "./UiLabel.tsx";
import LocaleSelector from "./UiLocaleSelector.tsx";
import {useT} from "../hooks/useT.ts";

interface AuthContextType {
    login: (username: string, password: string) => Promise<void>;
}

const Login = () => {
    const [formData, setFormData] = useState({email: '', password: ''});
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const {login} = useContext(AuthContext) as AuthContextType;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({...formData, [e.target.name]: e.target.value});
        // Clear error when user starts typing in credentials
        if (error) {
            setError(null);
        }
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await login(formData.email, formData.password);
            // If we reach here, login succeeded and navigation will happen
        } catch (err: any) {
            console.error('Login error:', err);
            const errorMessage = err.message || 'Login failed. Please check your credentials.';
            console.log('Setting error message:', errorMessage);
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const placeholderEnterYourEmail = useT("login.placeholder.enter_your_email");
    const placeholderEnterYourPassword = useT("login.placeholder.enter_your_password");

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <form
                onSubmit={handleSubmit}
                className="ace-card ace-card-strong ace-card-pad w-full max-w-md"
                autoComplete="on"
            >
                <h2 className="mb-6 text-center text-2xl font-bold text-slate-800 sm:text-3xl">
                    <UiLabel k="login.login"/>
                </h2>

                {error && (
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
                        {error}
                    </div>
                )}

                <label className="block mb-4">
                    <span className="ace-field-label"><UiLabel k="login.email"/></span>
                    <input
                        type="text"
                        name="email"
                        id="email"
                        placeholder={placeholderEnterYourEmail}
                        autoComplete="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="ace-input"
                    />
                </label>

                <label className="block mb-4">
                    <span className="ace-field-label"><UiLabel k="login.password"/></span>
                    <input
                        type="password"
                        name="password"
                        id="password"
                        placeholder={placeholderEnterYourPassword}
                        autoComplete="current-password"
                        value={formData.password}
                        onChange={handleChange}
                        className="ace-input"
                    />
                </label>

                <label className="block mb-6">
                    <span className="ace-field-label"><UiLabel k="login.language"/></span>
                    <LocaleSelector/>
                </label>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="ace-primary-btn"
                >
                    {isLoading ? 'Logging in...' : <UiLabel k="login.button.login"/>}
                </button>

                <div className="mt-4 text-center">
                    <a
                        href="/forgot-password"
                        className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                    >
                        <UiLabel k="login.link.forgot_password"/>
                    </a>
                </div>
            </form>
        </div>
    );
};

export default Login;

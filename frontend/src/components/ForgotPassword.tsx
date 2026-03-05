// frontend/src/components/ForgotPassword.tsx

import React, {useState} from 'react';
import {Link} from 'react-router-dom';
import api from '../api/api';
import UiLabel from './UiLabel.tsx';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await api.post('/auth/forgot-password', { email });
            setSuccess(true);
        } catch (err: any) {
            if (err?.response?.status === 404) {
                // Hide user-enumeration signals if backend leaks "Not Found" for unknown emails.
                setSuccess(true);
                return;
            }
            setError('Failed to send reset email. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <div className="ace-page-shell flex items-center justify-center">
                <div className="ace-card ace-card-strong ace-card-pad w-full max-w-md">
                    <h2 className="mb-6 text-center text-2xl font-bold text-slate-800 sm:text-3xl">
                        <UiLabel k="forgot_password.title.check_email"/>
                    </h2>
                    <p className="text-gray-700 mb-6 text-center">
                        <UiLabel k="forgot_password.message.instructions_sent"/>
                    </p>
                    <Link
                        to="/login"
                        className="ace-primary-btn block text-center"
                    >
                        <UiLabel k="forgot_password.button.back_to_login"/>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <form
                onSubmit={handleSubmit}
                className="ace-card ace-card-strong ace-card-pad w-full max-w-md"
            >
                <h2 className="mb-6 text-center text-2xl font-bold text-slate-800 sm:text-3xl">
                    <UiLabel k="forgot_password.title.forgot_password"/>
                </h2>

                {error && (
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
                        {error}
                    </div>
                )}

                <label className="block mb-6">
                    <span className="ace-field-label"><UiLabel k="forgot_password.label.email"/></span>
                    <input
                        type="email"
                        name="email"
                        id="email"
                        autoComplete="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="ace-input"
                    />
                </label>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="ace-primary-btn mb-4"
                >
                    {isLoading ? <UiLabel k="forgot_password.button.sending"/> : <UiLabel k="forgot_password.button.send_reset_link"/>}
                </button>

                <div className="text-center">
                    <Link
                        to="/login"
                        className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                    >
                        <UiLabel k="forgot_password.link.back_to_login"/>
                    </Link>
                </div>
            </form>
        </div>
    );
};

export default ForgotPassword;

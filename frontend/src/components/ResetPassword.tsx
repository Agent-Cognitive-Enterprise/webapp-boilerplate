// frontend/src/components/ResetPassword.tsx

import React, {useState} from 'react';
import {Link, useSearchParams, useNavigate} from 'react-router-dom';
import api from '../api/api';
import UiLabel from './UiLabel.tsx';
import {useT} from '../hooks/useT.ts';

const ResetPassword = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get('token');

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const placeholderPassword = useT("reset_password.placeholder.new_password");
    const placeholderConfirmPassword = useT("reset_password.placeholder.confirm_password");

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (!token) {
            setError('Invalid reset token');
            return;
        }

        setIsLoading(true);

        try {
            await api.post('/auth/reset-password', {
                token,
                new_password: password,
            });
            // Redirect to login with success message
            navigate('/login?reset=success');
        } catch (err: any) {
            const detail = err.response?.data?.detail;
            if (typeof detail === 'object' && detail.message) {
                // Password validation errors
                const errors = detail.errors || [];
                setError(`${detail.message}: ${errors.join(', ')}`);
            } else {
                setError(detail || 'Failed to reset password. Please try again.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="ace-page-shell flex items-center justify-center">
                <div className="ace-card ace-card-strong ace-card-pad w-full max-w-md">
                    <h2 className="mb-6 text-center text-2xl font-bold text-slate-800 sm:text-3xl">
                        <UiLabel k="reset_password.title.invalid_link"/>
                    </h2>
                    <p className="text-gray-700 mb-6 text-center">
                        <UiLabel k="reset_password.message.link_invalid_or_expired"/>
                    </p>
                    <Link
                        to="/forgot-password"
                        className="ace-primary-btn block text-center"
                    >
                        <UiLabel k="reset_password.button.request_new_link"/>
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
                    <UiLabel k="reset_password.title.reset_password"/>
                </h2>

                {error && (
                    <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md text-sm">
                        {error}
                    </div>
                )}

                <label className="block mb-4">
                    <span className="ace-field-label"><UiLabel k="reset_password.label.new_password"/></span>
                    <input
                        type="password"
                        name="password"
                        id="password"
                        placeholder={placeholderPassword}
                        autoComplete="new-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        minLength={8}
                        className="ace-input"
                    />
                </label>

                <label className="block mb-6">
                    <span className="ace-field-label"><UiLabel k="reset_password.label.confirm_password"/></span>
                    <input
                        type="password"
                        name="confirmPassword"
                        id="confirmPassword"
                        placeholder={placeholderConfirmPassword}
                        autoComplete="new-password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        minLength={8}
                        className="ace-input"
                    />
                </label>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="ace-primary-btn mb-4"
                >
                    {isLoading ? <UiLabel k="reset_password.button.resetting"/> : <UiLabel k="reset_password.button.reset_password"/>}
                </button>

                <div className="text-center">
                    <Link
                        to="/login"
                        className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                    >
                        <UiLabel k="reset_password.link.back_to_login"/>
                    </Link>
                </div>
            </form>
        </div>
    );
};

export default ResetPassword;

// frontend/src/components/Register.tsx

import React, {useState, useContext} from 'react';
import {AuthContext} from '../contexts/AuthContext.tsx';
import LocaleSelector from "./UiLocaleSelector.tsx";
import UiLabel from "./UiLabel.tsx";
import {useT} from "../hooks/useT.ts";

interface AuthContextType {
    register: (full_name: string, email: string, password: string) => void;
}

const Register = () => {
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        password: ''
    });

    const {register} = useContext(AuthContext) as AuthContextType;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({...formData, [e.target.name]: e.target.value});
    };

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        register(formData.full_name, formData.email, formData.password);
    };

    const placeholderEnterYourFullName = useT("register.placeholder.enter_your_full_name");
    const placeholderEnterYourEmail = useT("register.placeholder.enter_your_email");
    const placeholderEnterYourPassword = useT("register.placeholder.enter_your_password");

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <form
                onSubmit={handleSubmit}
                className="ace-card ace-card-strong ace-card-pad w-full max-w-md"
            >
                <h2 className="mb-6 text-center text-2xl font-bold text-slate-800 sm:text-3xl">
                    <UiLabel k="register.title.register"/>
                </h2>

                <label className="block mb-4">
                    <span className="ace-field-label">
                        <UiLabel k="register.label.language"/>
                    </span>
                    <LocaleSelector/>
                </label>

                <label className="block mb-4">
                    <span className="ace-field-label">
                        <UiLabel k="register.lable.full_name"/>
                    </span>
                    <input
                        type="text"
                        name="full_name"
                        placeholder={placeholderEnterYourFullName}
                        value={formData.full_name}
                        onChange={handleChange}
                        className="ace-input"
                    />
                </label>

                <label className="block mb-4">
                    <span className="ace-field-label">
                        <UiLabel k="register.label.email" />
                    </span>
                    <input
                        type="email"
                        name="email"
                        placeholder={placeholderEnterYourEmail}
                        value={formData.email}
                        onChange={handleChange}
                        className="ace-input"
                    />
                </label>

                <label className="block mb-6">
                    <span className="ace-field-label">
                        <UiLabel k="register.label.password" />
                    </span>
                    <input
                        type="password"
                        name="password"
                        placeholder={placeholderEnterYourPassword}
                        value={formData.password}
                        onChange={handleChange}
                        className="ace-input"
                    />
                </label>

                <button
                    type="submit"
                    className="ace-primary-btn"
                >
                    <UiLabel k="register.button.register" />
                </button>
            </form>
        </div>
    );
};

export default Register;

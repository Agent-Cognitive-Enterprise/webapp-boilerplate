import UiLabel from "./UiLabel.tsx";
import LocaleSelector from "./UiLocaleSelector.tsx";
import {useLoginForm} from "./login/useLoginForm.ts";

const Login = () => {
    const {
        formData,
        error,
        isLoading,
        handleChange,
        handleSubmit,
        placeholderEnterYourEmail,
        placeholderEnterYourPassword,
    } = useLoginForm();

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

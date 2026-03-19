import LocaleSelector from "./UiLocaleSelector.tsx";
import UiLabel from "./UiLabel.tsx";
import {useRegisterForm} from "./register/useRegisterForm.ts";

const Register = () => {
    const {
        formData,
        error,
        handleChange,
        handleSubmit,
        placeholderEnterYourFullName,
        placeholderEnterYourEmail,
        placeholderEnterYourPassword,
    } = useRegisterForm();

    return (
        <div className="ace-page-shell flex items-center justify-center">
            <form
                onSubmit={handleSubmit}
                className="ace-card ace-card-strong ace-card-pad w-full max-w-md"
            >
                <h2 className="mb-6 text-center text-2xl font-bold text-slate-800 sm:text-3xl">
                    <UiLabel k="register.title.register"/>
                </h2>

                {error && (
                    <div className="mb-4 rounded-md border border-red-400 bg-red-100 p-3 text-red-700">
                        {error}
                    </div>
                )}

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

import {useContext, useEffect, useMemo, useRef, useState} from "react";
import {AuthContext} from "../../../contexts/AuthContext.tsx";
import {useUiLabelContext} from "../../../contexts/UiLabelProvider.tsx";
import {useUiLabel} from "../../../hooks/useUiLabel.ts";
import {getUiLabelKeyTail} from "../../../hooks/useUiLabelText.ts";

type UseTranslationModalStateArgs = {
    keyName: string;
    locale: string;
    currentValue?: string;
};

export function useTranslationModalState({
    keyName,
    locale,
    currentValue,
}: UseTranslationModalStateArgs) {
    const auth = useContext(AuthContext);

    if (!auth) {
        throw new Error("AuthContext not available");
    }

    const {token} = auth;
    const {suggest} = useUiLabelContext();
    const {value: englishValue} = useUiLabel(keyName, "en");
    const {value: localeValue} = useUiLabel(keyName, locale);

    const userEditedRef = useRef(false);
    const [text, setText] = useState<string>(currentValue ?? localeValue ?? "");

    useEffect(() => {
        if (!userEditedRef.current && text === "" && localeValue) {
            setText(localeValue);
        }
    }, [localeValue, text]);

    const keyNameTail = useMemo(() => getUiLabelKeyTail(keyName), [keyName]);

    const setDraftValue = (value: string) => {
        userEditedRef.current = true;
        setText(value);
    };

    const submitSuggestion = async (): Promise<void> => {
        await suggest(keyName, locale, text);
    };

    return {
        token,
        englishValue,
        localeValue,
        keyNameTail,
        text,
        setDraftValue,
        submitSuggestion,
    };
}

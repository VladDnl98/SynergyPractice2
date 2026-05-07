function getRussianValidationMessage(input) {
    const { validity } = input;

    if (validity.valueMissing) {
        return "Пожалуйста, заполните это поле.";
    }
    if (validity.typeMismatch) {
        if (input.type === "email") return "Введите корректный адрес электронной почты.";
        if (input.type === "url") return "Введите корректный URL.";
        return "Введите значение в правильном формате.";
    }
    if (validity.badInput) {
        if (input.type === "number") return "Введите число.";
        return "Введите корректное значение.";
    }
    if (validity.rangeUnderflow) {
        return `Значение должно быть не меньше ${input.min}.`;
    }
    if (validity.rangeOverflow) {
        return `Значение должно быть не больше ${input.max}.`;
    }
    if (validity.stepMismatch) {
        return "Введите корректное значение с допустимым шагом.";
    }
    if (validity.tooShort) {
        return `Минимальная длина: ${input.minLength} символов.`;
    }
    if (validity.tooLong) {
        return `Максимальная длина: ${input.maxLength} символов.`;
    }
    if (validity.patternMismatch) {
        return "Значение не соответствует требуемому формату.";
    }
    return "";
}

function enableRussianValidationMessages() {
    const forms = document.querySelectorAll("form");
    forms.forEach((form) => {
        const controls = form.querySelectorAll("input, select, textarea");

        controls.forEach((control) => {
            control.addEventListener("input", () => control.setCustomValidity(""));
            control.addEventListener("change", () => control.setCustomValidity(""));
            control.addEventListener("invalid", () => {
                control.setCustomValidity(getRussianValidationMessage(control));
            });
        });

        form.addEventListener("submit", (event) => {
            let hasError = false;
            controls.forEach((control) => {
                control.setCustomValidity("");
                if (!control.checkValidity()) {
                    control.setCustomValidity(getRussianValidationMessage(control));
                    hasError = true;
                }
            });
            if (hasError) {
                event.preventDefault();
                form.reportValidity();
            }
        });
    });
}

enableRussianValidationMessages();

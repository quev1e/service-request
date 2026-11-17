document.addEventListener("click", (event) => {
    const button = event.target.closest(".attachment-button");

    if (!button) {
        return;
    }

    const input = button.nextElementSibling;

    if (input && input.type === "file") {
        input.click();
    }
});

document.addEventListener("change", (event) => {
    const input = event.target;

    if (!input.matches(".attachment-fields input[type='file']")) {
        return;
    }

    const field = input.closest(".attachment-fields");
    const buttonText = field.querySelector(".attachment-button-text");
    const nextField = field.nextElementSibling;

    if (input.files.length > 0) {
        buttonText.textContent = input.files[0].name;
        field.classList.add("has-file");

        if (nextField) {
            nextField.classList.remove("hidden");
        }
    } else {
        buttonText.textContent = "Прикрепить файл";
        field.classList.remove("has-file");
    }
});


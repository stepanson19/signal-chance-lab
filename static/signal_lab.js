function randomizeLabValue(config) {
    const step = config.step || 1;
    const span = config.max - config.min;
    const steps = Math.round(span / step);
    const offset = Math.floor(Math.random() * (steps + 1));
    const rawValue = config.min + (offset * step);
    if (config.type === "int") {
        return Math.round(rawValue);
    }
    const decimals = config.decimals || 2;
    return rawValue.toFixed(decimals);
}

function applyPreset(form, values) {
    Object.entries(values).forEach(([fieldName, fieldValue]) => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.value = fieldValue;
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-lab-form]");
    if (!form) {
        return;
    }

    const randomConfigNode = document.getElementById("lab-random-fill");
    const presetsNode = document.getElementById("lab-presets");
    const feedback = document.querySelector("[data-lab-feedback]");
    const randomButton = document.querySelector("[data-random-fill-trigger]");

    const randomConfig = randomConfigNode ? JSON.parse(randomConfigNode.textContent) : {};
    const presets = presetsNode ? JSON.parse(presetsNode.textContent) : [];

    if (randomButton) {
        randomButton.addEventListener("click", () => {
            Object.entries(randomConfig).forEach(([fieldName, config]) => {
                applyPreset(form, {
                    [fieldName]: randomizeLabValue(config),
                });
            });
            if (feedback) {
                feedback.textContent = "Параметры случайно собраны. Можно сразу запускать эксперимент.";
            }
        });
    }

    document.querySelectorAll("[data-preset-index]").forEach((button) => {
        button.addEventListener("click", () => {
            const preset = presets[Number(button.dataset.presetIndex)];
            if (!preset) {
                return;
            }
            applyPreset(form, preset.values);
            if (feedback) {
                feedback.textContent = `Применен пресет: ${preset.label}.`;
            }
        });
    });
});

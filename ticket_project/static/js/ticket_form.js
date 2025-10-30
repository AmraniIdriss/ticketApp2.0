// template_fields.js

document.addEventListener("DOMContentLoaded", () => {
    const activityTypeSelect = document.getElementById("activity_type");
    const templateFieldsDiv = document.getElementById("templateFields");
    const form = document.getElementById("ticketForm");
    const activityResolutionTextarea = document.getElementById("activity_resolution_description");

    // Define os templates com os campos que devem aparecer
    const activityTemplates = {
        "♣ Development": ["Target", "Observations"],
        "♦ Release Deployment": ["Target", "Observations"],
        "Project": ["Target", "Observations"],
        "Maintenance Activity": ["Maintenance Details", "Observations"],
        "☛ Solicitation": ["Request Details", "Observations"],
        "⚠️ Incident": ["Reported Issue", "Observations"],
        "☠ Trouble Ticket": ["Problem Details", "Error Description"]
    };

    // Função para criar campos dinamicamente
    function renderTemplateFields(selectedType) {
        templateFieldsDiv.innerHTML = ""; // limpa campos anteriores

        if (activityTemplates[selectedType]) {
            activityTemplates[selectedType].forEach(fieldName => {
                const div = document.createElement("div");
                div.classList.add("mb-3");

                const label = document.createElement("label");
                label.classList.add("form-label");
                label.textContent = fieldName;

                const input = document.createElement("input");
                input.type = "text";
                input.classList.add("form-control");
                input.setAttribute("placeholder", fieldName);
                input.setAttribute("data-template-field", fieldName);

                div.appendChild(label);
                div.appendChild(input);
                templateFieldsDiv.appendChild(div);
            });
        }
    }

    // Atualiza os campos quando o Activity Type muda
    activityTypeSelect.addEventListener("change", (e) => {
        const selectedType = e.target.value;
        renderTemplateFields(selectedType);
    });

    // Antes de submeter o form, concatena os valores dos campos no textarea
    form.addEventListener("submit", (e) => {
        const templateInputs = templateFieldsDiv.querySelectorAll("input[data-template-field]");
        let combinedText = "";

        templateInputs.forEach(input => {
            combinedText += `${input.getAttribute("data-template-field")}: ${input.value}\n`;
        });

        activityResolutionTextarea.value = combinedText.trim();
    });
});

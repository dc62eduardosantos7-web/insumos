document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.querySelector("[data-menu-button]");
    const menu = document.querySelector("[data-menu]");
    if (menuButton && menu) {
        menuButton.addEventListener("click", () => menu.classList.toggle("open"));
    }

    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => {
            const button = form.querySelector("button[type='submit']");
            if (button) {
                button.disabled = true;
                button.dataset.originalText = button.textContent;
                button.textContent = "Processando…";
            }
        });
    });

    const rows = document.querySelector("[data-formset-rows]");
    const emptyForm = document.querySelector("[data-empty-form]");
    const addForm = document.querySelector("[data-add-form]");
    const totalForms = document.querySelector("[name='itens-TOTAL_FORMS']");
    if (rows && emptyForm && addForm && totalForms) {
        addForm.addEventListener("click", () => {
            const index = Number(totalForms.value);
            const html = emptyForm.innerHTML.replaceAll("__prefix__", index);
            rows.insertAdjacentHTML("beforeend", html);
            totalForms.value = index + 1;
        });

        rows.addEventListener("click", (event) => {
            const button = event.target.closest("[data-remove-form]");
            if (!button || rows.children.length === 1) return;
            button.closest("tr").remove();
            [...rows.children].forEach((row, index) => {
                row.querySelectorAll("input, select, textarea, label").forEach((field) => {
                    if (field.name) field.name = field.name.replace(/itens-\d+-/, `itens-${index}-`);
                    if (field.id) field.id = field.id.replace(/itens-\d+-/, `itens-${index}-`);
                    if (field.htmlFor) field.htmlFor = field.htmlFor.replace(/itens-\d+-/, `itens-${index}-`);
                });
            });
            totalForms.value = rows.children.length;
        });
    }

    window.setTimeout(() => {
        document.querySelectorAll(".message").forEach((message) => {
            message.classList.add("hide");
        });
    }, 5000);
});

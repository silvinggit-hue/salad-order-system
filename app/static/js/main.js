document.addEventListener("DOMContentLoaded", function () {
    const qtyButtons = document.querySelectorAll(".qty-btn");

    qtyButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const targetId = this.dataset.target;
            const input = document.getElementById(targetId);

            if (!input) return;

            let currentValue = parseInt(input.value || "0", 10);
            if (isNaN(currentValue)) currentValue = 0;

            if (this.classList.contains("plus-btn")) {
                input.value = currentValue + 1;
            }

            if (this.classList.contains("minus-btn")) {
                input.value = Math.max(0, currentValue - 1);
            }

            input.dispatchEvent(new Event("change"));
        });
    });
});
document.addEventListener("DOMContentLoaded", function () {
    const qtyButtons = document.querySelectorAll(".qty-btn");
    const qtyInputs = document.querySelectorAll(".qty-input");
    const totalPriceEl = document.getElementById("live-total-price");

    function updateTotalPrice() {
        let total = 0;

        qtyInputs.forEach((input) => {
            const quantity = parseInt(input.value || "0", 10);
            const price = parseInt(input.dataset.price || "0", 10);

            if (!isNaN(quantity) && !isNaN(price) && quantity > 0) {
                total += quantity * price;
            }
        });

        if (totalPriceEl) {
            totalPriceEl.textContent = total.toLocaleString("ko-KR");
        }
    }

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

            updateTotalPrice();
        });
    });

    qtyInputs.forEach((input) => {
        input.addEventListener("input", updateTotalPrice);
        input.addEventListener("change", updateTotalPrice);
    });

    updateTotalPrice();
});

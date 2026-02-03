const formatMoney = (value) => value.toFixed(2);

const computeTotals = () => {
  const items = document.querySelectorAll(".penalty-item:checked");
  let checklistTotal = 0;

  items.forEach((item) => {
    if (item.dataset.skipTotal === "true") {
      return;
    }
    const amount = Number(item.dataset.amount || 0);
    checklistTotal += amount;
  });

  const grandTotal = checklistTotal;

  document.getElementById("checklistTotal").textContent = formatMoney(checklistTotal);
  document.getElementById("grandTotal").textContent = formatMoney(grandTotal);
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".penalty-item").forEach((item) => {
    item.addEventListener("change", computeTotals);
  });

  const lodgingDaysInput = document.getElementById("lodgingDays");
  const lodgingToggle = document.querySelector('[data-role="lodging"]');

  if (lodgingDaysInput) {
    lodgingDaysInput.addEventListener("input", computeTotals);
  }

  if (lodgingToggle) {
    lodgingToggle.addEventListener("change", () => {
      if (lodgingDaysInput) {
        lodgingDaysInput.disabled = !lodgingToggle.checked;
      }
      computeTotals();
    });
  }

  if (lodgingToggle && lodgingDaysInput) {
    lodgingDaysInput.disabled = !lodgingToggle.checked;
  }

  computeTotals();
});

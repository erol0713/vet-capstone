const formatMoney = (value) => value.toFixed(2);

const computeTotals = () => {
  const checkedItems = document.querySelectorAll(".penalty-item:checked");
  let checklistTotal = 0;

  checkedItems.forEach((item) => {
    if (item.dataset.skipTotal === "true") {
      return;
    }
    const amount = Number(item.dataset.amount || 0);
    checklistTotal += amount;
  });

  let lodgingTotal = 0;
  const lodgingToggle = document.querySelector('[data-role="lodging"]');
  const lodgingDaysInput = document.getElementById("lodgingDays");
  const lodgingRateInput = document.getElementById("lodgingRateInput");
  const hasLodging = Boolean(lodgingToggle && lodgingToggle.checked);

  if (hasLodging && lodgingDaysInput && lodgingRateInput) {
    const days = Number(lodgingDaysInput.value || 0);
    const rate = Number(lodgingRateInput.value || 0);
    lodgingTotal = days * rate;
  }

  const grandTotal = checklistTotal + lodgingTotal;
  const lodgingDays = hasLodging && lodgingDaysInput ? Number(lodgingDaysInput.value || 0) : 0;

  document.getElementById("checklistTotal").textContent = formatMoney(checklistTotal);
  const lodgingTotalNode = document.getElementById("lodgingTotal");
  if (lodgingTotalNode) {
    lodgingTotalNode.textContent = formatMoney(lodgingTotal);
  }
  document.getElementById("grandTotal").textContent = formatMoney(grandTotal);
  const selectedCountNode = document.getElementById("selectedCount");
  if (selectedCountNode) {
    selectedCountNode.textContent = String(checkedItems.length);
  }
  const lodgingDaysNode = document.getElementById("lodgingDaysDisplay");
  if (lodgingDaysNode) {
    lodgingDaysNode.textContent = String(lodgingDays);
  }
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

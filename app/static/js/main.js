/* app/static/js/main.js */

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      alert.style.transition = 'all 0.3s ease';
      setTimeout(() => alert.remove(), 300);
    }, 6000);
  });

  // Dynamic Line Item Addition for Receipts / Deliveries / Transfers
  const addLineBtn = document.getElementById('add-line-btn');
  const lineItemsContainer = document.getElementById('line-items-tbody');

  if (addLineBtn && lineItemsContainer) {
    addLineBtn.addEventListener('click', () => {
      const firstRow = lineItemsContainer.querySelector('tr');
      if (firstRow) {
        const newRow = firstRow.cloneNode(true);
        // Clear input values in cloned row
        const inputs = newRow.querySelectorAll('input');
        inputs.forEach(input => input.value = '');
        
        // Reset select element if any
        const selects = newRow.querySelectorAll('select');
        selects.forEach(select => select.selectedIndex = 0);

        lineItemsContainer.appendChild(newRow);
        attachRowRemoveHandlers();
      }
    });
    attachRowRemoveHandlers();
  }

  function attachRowRemoveHandlers() {
    const removeBtns = document.querySelectorAll('.remove-line-btn');
    removeBtns.forEach(btn => {
      btn.onclick = function() {
        const tbody = this.closest('tbody');
        if (tbody.querySelectorAll('tr').length > 1) {
          this.closest('tr').remove();
        } else {
          alert('At least one product line item is required.');
        }
      };
    });
  }

  // Adjustment Form Live Stock Fetcher
  const adjLocationSelect = document.getElementById('adj_location_id');
  const adjProductSelect = document.getElementById('adj_product_id');
  const recordedQtyInput = document.getElementById('recorded_quantity_display');

  if (adjLocationSelect && adjProductSelect && recordedQtyInput) {
    function updateRecordedStock() {
      const locationId = adjLocationSelect.value;
      const productId = adjProductSelect.value;

      if (locationId && productId) {
        fetch(`/adjustments/api/get-stock?product_id=${productId}&location_id=${locationId}`)
          .then(res => res.json())
          .then(data => {
            recordedQtyInput.value = data.recorded_quantity;
            calculateDifference();
          })
          .catch(err => console.error('Error fetching stock:', err));
      }
    }

    adjLocationSelect.addEventListener('change', updateRecordedStock);
    adjProductSelect.addEventListener('change', updateRecordedStock);

    const countedQtyInput = document.getElementById('counted_quantity');
    const diffDisplay = document.getElementById('difference_display');

    function calculateDifference() {
      if (recordedQtyInput && countedQtyInput && diffDisplay) {
        const recorded = parseFloat(recordedQtyInput.value) || 0;
        const counted = parseFloat(countedQtyInput.value) || 0;
        const diff = counted - recorded;
        diffDisplay.value = (diff >= 0 ? '+' : '') + diff;
      }
    }

    if (countedQtyInput) {
      countedQtyInput.addEventListener('input', calculateDifference);
    }
  }
});

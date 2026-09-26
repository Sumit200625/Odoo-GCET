/* app/static/js/assistant.js - Global Command Center & Natural-Language Assistant */

document.addEventListener('DOMContentLoaded', () => {
    // Keyboard shortcut Ctrl+K / Cmd+K to activate Assistant
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            openAssistantModal();
        }
    });

    const globalSearchInput = document.getElementById('globalSearch');
    if (globalSearchInput) {
        globalSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const q = globalSearchInput.value.trim();
                if (q) {
                    openAssistantModal(q);
                }
            }
        });
    }
});

function openAssistantModal(initialQuery = '') {
    let modalEl = document.getElementById('assistantModal');
    if (!modalEl) {
        modalEl = createAssistantModalDOM();
        document.body.appendChild(modalEl);
    }

    const modalInput = document.getElementById('assistantQueryInput');
    if (initialQuery) {
        modalInput.value = initialQuery;
        submitAssistantQuery(initialQuery);
    } else {
        modalInput.value = '';
    }

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
    setTimeout(() => modalInput.focus(), 300);
}

function createAssistantModalDOM() {
    const div = document.createElement('div');
    div.className = 'modal fade';
    div.id = 'assistantModal';
    div.tabIndex = -1;
    div.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content border-0 shadow-lg bg-dark text-white">
                <div class="modal-header border-secondary py-3">
                    <h5 class="modal-title fw-bold text-warning"><i class="bi bi-cpu me-2"></i>StockSense AI Natural-Language Assistant</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-4">
                    <div class="input-group input-group-lg mb-3">
                        <input type="text" id="assistantQueryInput" class="form-control bg-secondary text-white border-0" 
                               placeholder="Ask e.g. 'Which products may stock out this week?' or 'Show expiring grocery items'...">
                        <button class="btn btn-warning fw-bold px-4" type="button" onclick="handleAssistantSubmit()"><i class="bi bi-send me-1"></i> Ask AI</button>
                    </div>

                    <div class="d-flex flex-wrap gap-2 mb-4">
                        <span class="badge bg-outline-light text-light border cursor-pointer" onclick="fillQuery(this.innerText)">Which products may stock out this week?</span>
                        <span class="badge bg-outline-light text-light border cursor-pointer" onclick="fillQuery(this.innerText)">Show grocery products expiring within 15 days</span>
                        <span class="badge bg-outline-light text-light border cursor-pointer" onclick="fillQuery(this.innerText)">What should I reorder before Diwali?</span>
                        <span class="badge bg-outline-light text-light border cursor-pointer" onclick="fillQuery(this.innerText)">Which supplier has best delivery reliability?</span>
                    </div>

                    <div id="assistantResponseContainer" class="p-3 bg-black bg-opacity-50 rounded min-h-150">
                        <div class="text-center text-muted py-4">
                            <i class="bi bi-chat-left-dots fs-1 d-block mb-2 text-warning opacity-50"></i>
                            Type a question above or click an example prompt to get explainable AI intelligence.
                        </div>
                    </div>
                </div>
                <div class="modal-footer border-secondary py-2 justify-content-between">
                    <small class="text-muted"><i class="bi bi-command me-1"></i>Press <kbd class="bg-secondary text-white">Ctrl+K</kbd> anytime to open Assistant</small>
                    <button type="button" class="btn btn-sm btn-outline-light" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    return div;
}

function fillQuery(text) {
    const input = document.getElementById('assistantQueryInput');
    if (input) {
        input.value = text;
        submitAssistantQuery(text);
    }
}

function handleAssistantSubmit() {
    const input = document.getElementById('assistantQueryInput');
    if (input && input.value.trim()) {
        submitAssistantQuery(input.value.trim());
    }
}

function submitAssistantQuery(queryText) {
    const container = document.getElementById('assistantResponseContainer');
    if (!container) return;

    container.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-warning mb-2" role="status"></div>
            <p class="text-muted mb-0 small">Querying StockSense AI Intelligence Engine & Database...</p>
        </div>
    `;

    fetch('/api/v1/assistant/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ query: queryText })
    })
    .then(res => res.json())
    .then(data => {
        let recordsHtml = '';
        if (data.records && data.records.length > 0) {
            recordsHtml = `
                <div class="mt-3 pt-3 border-top border-secondary">
                    <h6 class="fw-bold text-warning mb-2"><i class="bi bi-database-check me-1"></i>Related Database Records (${data.records.length}):</h6>
                    <div class="list-group list-group-flush">
                        ${data.records.map(r => `
                            <div class="list-group-item bg-dark text-white border-secondary py-2 d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${r.name || r.sku || 'Record #' + r.id}</strong>
                                    ${r.sku ? `<small class="text-muted ms-2">SKU: ${r.sku}</small>` : ''}
                                </div>
                                <span class="badge bg-secondary">${r.category || r.status || 'Active'}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        container.innerHTML = `
            <div class="text-white">
                <div class="d-flex align-items-center mb-2">
                    <span class="badge bg-warning text-dark me-2">AI Intent: ${data.intent || 'General Query'}</span>
                </div>
                <p class="fs-6 mb-2 lh-base" style="white-space: pre-line;">${data.answer || 'No response generated.'}</p>
                ${recordsHtml}
            </div>
        `;
    })
    .catch(err => {
        container.innerHTML = `
            <div class="alert alert-danger mb-0">
                <i class="bi bi-exclamation-triangle-fill me-2"></i> Failed to communicate with AI Assistant service.
            </div>
        `;
    });
}

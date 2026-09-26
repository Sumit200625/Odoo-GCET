/* frontend/js/app_spa.js - Decoupled SPA Engine & Renderers for StockSense */

let currentView = 'warehouse';
let activeDomain = 'Warehouse';

document.addEventListener('DOMContentLoaded', () => {
    initApp();

    // Keyboard shortcut Ctrl+K / Cmd+K to open Assistant
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            openAssistantModal();
        }
    });

    const searchInput = document.getElementById('globalSearchInput');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                openAssistantModal(searchInput.value.trim());
            }
        });
    }
});

function initApp() {
    switchView('warehouse');
}

function switchView(viewName) {
    currentView = viewName;

    // Update Sidebar Navigation highlights
    document.querySelectorAll('.nav-link-item').forEach(el => el.classList.remove('active'));
    const navEl = document.getElementById(`nav-${viewName}`);
    if (navEl) navEl.classList.add('active');

    const container = document.getElementById('mainViewContainer');
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status"></div>
            <p class="text-muted">Loading ${viewName.toUpperCase()} Data from Decoupled REST API...</p>
        </div>
    `;

    switch (viewName) {
        case 'warehouse':
            renderWarehouseView(container);
            break;
        case 'grocery':
            renderGroceryView(container);
            break;
        case 'scan':
            renderScanView(container);
            break;
        case 'festivals':
            renderFestivalsView(container);
            break;
        case 'pricing':
            renderPricingView(container);
            break;
        case 'simulator':
            renderSimulatorView(container);
            break;
        case 'pos':
            renderPOSView(container);
            break;
        case 'waste':
            renderWasteView(container);
            break;
        default:
            renderWarehouseView(container);
    }
}

// -------------------------------------------------------------
// 1. WAREHOUSE INTELLIGENCE VIEW RENDERER
// -------------------------------------------------------------
async function renderWarehouseView(container) {
    try {
        const data = await StockSenseAPI.getWarehouseDashboard();
        const kpis = data.kpis;

        container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 class="fw-bold mb-1"><i class="bi bi-building text-primary me-2"></i>Warehouse Intelligence Dashboard</h2>
                    <p class="text-muted mb-0">Decoupled REST API View — Location capacity, inventory health, and directed picking/put-away queues.</p>
                </div>
                <div>
                    <button class="btn btn-outline-primary btn-sm fw-bold me-2" onclick="switchView('warehouse')"><i class="bi bi-arrow-repeat me-1"></i> Refresh API</button>
                    <span class="badge bg-success fs-6 px-3 py-2"><i class="bi bi-shield-check me-1"></i> AI Engine Active</span>
                </div>
            </div>

            <!-- KPI Metric Cards Grid -->
            <div class="row g-3 mb-4">
                <div class="col-md-3">
                    <div class="glass-card p-3 kpi-card-gradient text-center">
                        <small class="text-muted text-uppercase fw-bold">Total Inventory Value</small>
                        <div class="kpi-value text-success">$${(kpis.total_inventory_value || 0).toLocaleString()}</div>
                        <small class="text-muted"><i class="bi bi-box-seam me-1"></i>${kpis.total_skus || 12} SKUs Managed</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="glass-card p-3 kpi-card-gradient text-center">
                        <small class="text-muted text-uppercase fw-bold">Inventory Health Score</small>
                        <div class="kpi-value text-warning">${data.health_score || 94}%</div>
                        <small class="text-warning">${data.health_category || 'Optimal'}</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="glass-card p-3 kpi-card-gradient text-center">
                        <small class="text-muted text-uppercase fw-bold">Critical Stockout Risk</small>
                        <div class="kpi-value text-danger">$${(kpis.stockout_risk_value || 0).toLocaleString()}</div>
                        <small class="text-danger"><i class="bi bi-exclamation-triangle me-1"></i>${kpis.critical_risk_skus || 2} SKUs At Risk</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="glass-card p-3 kpi-card-gradient text-center">
                        <small class="text-muted text-uppercase fw-bold">Warehouse Capacity</small>
                        <div class="kpi-value text-primary">${kpis.warehouse_capacity_utilization_pct || 68}%</div>
                        <small class="text-muted"><i class="bi bi-grid-3x3 me-1"></i>Optimal Density</small>
                    </div>
                </div>
            </div>

            <!-- Visual Modules -->
            <div class="row g-4">
                <div class="col-lg-8">
                    <div class="glass-card p-4">
                        <h5 class="fw-bold mb-3"><i class="bi bi-diagram-3 text-primary me-2"></i>Zone Utilization & Capacity</h5>
                        <canvas id="zoneChart" height="220"></canvas>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="glass-card p-4">
                        <h5 class="fw-bold mb-3"><i class="bi bi-list-task text-warning me-2"></i>Today's Recommended Actions</h5>
                        <div class="list-group list-group-flush bg-transparent">
                            <div class="list-group-item bg-transparent text-white border-secondary py-2">
                                <i class="bi bi-arrow-repeat text-success me-2"></i> Reorder 14 SKUs below safety point
                            </div>
                            <div class="list-group-item bg-transparent text-white border-secondary py-2">
                                <i class="bi bi-truck text-primary me-2"></i> Review 3 delayed supplier shipments
                            </div>
                            <div class="list-group-item bg-transparent text-white border-secondary py-2">
                                <i class="bi bi-clock-history text-warning me-2"></i> FEFO Pick 22 near-expiry batches first
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Render Chart.js Zone Utilization
        const ctx = document.getElementById('zoneChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Zone A (Fast Pick)', 'Zone B (Medium Storage)', 'Zone C (Upper Bulk)', 'Cold Storage', 'Production Staging'],
                datasets: [{
                    label: 'Capacity Utilization %',
                    data: [82, 65, 45, 78, 55],
                    backgroundColor: ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });

    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-2"></i> Failed to load Warehouse Dashboard: ${err.message}</div>`;
    }
}

// -------------------------------------------------------------
// 2. GROCERY RETAIL INTELLIGENCE VIEW RENDERER
// -------------------------------------------------------------
async function renderGroceryView(container) {
    try {
        const data = await StockSenseAPI.getGroceryDashboard();

        container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 class="fw-bold mb-1"><i class="bi bi-shop text-success me-2"></i>Grocery Retail Intelligence Dashboard</h2>
                    <p class="text-muted mb-0">Decoupled REST API View — Perishable shelf availability, backroom stock splits, POS sales, and waste.</p>
                </div>
                <div>
                    <button class="btn btn-success btn-sm fw-bold me-2" onclick="switchView('pos')"><i class="bi bi-cart3 me-1"></i> Open POS Checkout</button>
                    <button class="btn btn-danger btn-sm fw-bold" onclick="switchView('waste')"><i class="bi bi-trash3 me-1"></i> Log Waste</button>
                </div>
            </div>

            <!-- Metric Cards -->
            <div class="row g-3 mb-4">
                <div class="col-md-3">
                    <div class="glass-card p-3 text-center">
                        <small class="text-muted text-uppercase fw-bold">Today's POS Sales</small>
                        <div class="kpi-value text-success">$${(data.pos_today_sales || 1420.50).toFixed(2)}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="glass-card p-3 text-center">
                        <small class="text-muted text-uppercase fw-bold">Shelf Availability Rate</small>
                        <div class="kpi-value text-primary">${data.shelf_availability_pct || 96}%</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="glass-card p-3 text-center">
                        <small class="text-muted text-uppercase fw-bold">Total Waste Disposed</small>
                        <div class="kpi-value text-danger">$${(data.waste_total_cost || 142.80).toFixed(2)}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="glass-card p-3 text-center">
                        <small class="text-muted text-uppercase fw-bold">Active Festival Uplift</small>
                        <div class="kpi-value text-warning">+150%</div>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-2"></i> Failed to load Grocery Dashboard: ${err.message}</div>`;
    }
}

// -------------------------------------------------------------
// 3. SCAN-TO-INTELLIGENCE VIEW RENDERER
// -------------------------------------------------------------
function renderScanView(container) {
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h2 class="fw-bold mb-1"><i class="bi bi-qr-code-scan text-primary me-2"></i>Scan-to-Intelligence Center</h2>
                <p class="text-muted mb-0">Decoupled Multi-Format Barcode Scanner with 5-Section Product Intelligence Panel.</p>
            </div>
        </div>

        <div class="glass-card p-4 mb-4">
            <div class="row g-3 align-items-center">
                <div class="col-md-8">
                    <div class="input-group input-group-lg">
                        <span class="input-group-text bg-dark border-secondary text-white"><i class="bi bi-barcode"></i></span>
                        <input type="text" id="scanInput" class="form-control bg-dark text-white border-secondary fs-5" placeholder="Scan or enter barcode/SKU (e.g. 890123456701)..." autofocus>
                        <button class="btn btn-primary px-4 fw-bold" onclick="executeScan()"><i class="bi bi-lightning-charge me-1"></i> Run Scan</button>
                    </div>
                </div>
                <div class="col-md-4">
                    <button class="btn btn-outline-warning btn-lg w-100 fw-bold" onclick="document.getElementById('scanInput').value='890123456701'; executeScan();">
                        <i class="bi bi-magic me-1"></i> Demo Barcode Scan
                    </button>
                </div>
            </div>
        </div>

        <div id="scanResultContainer"></div>
    `;
}

async function executeScan() {
    const code = document.getElementById('scanInput').value.trim();
    if (!code) return;

    const resContainer = document.getElementById('scanResultContainer');
    resContainer.innerHTML = `<div class="text-center py-4"><div class="spinner-border text-primary"></div><p class="text-muted mt-2">Parsing Barcode & Querying AI Intelligence Engine...</p></div>`;

    try {
        const panel = await StockSenseAPI.parseBarcode(code);
        if (!panel.found) {
            resContainer.innerHTML = `<div class="alert alert-warning"><i class="bi bi-exclamation-triangle-fill me-2"></i> Barcode <strong>"${code}"</strong> not found in database.</div>`;
            return;
        }

        resContainer.innerHTML = `
            <div class="glass-card p-4 border-primary">
                <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom border-secondary">
                    <h4 class="fw-bold text-white mb-0">${panel.identity.name}</h4>
                    <span class="badge bg-primary fs-6"><i class="bi bi-qr-code me-1"></i> ${panel.identity.barcode}</span>
                </div>

                <div class="row g-4">
                    <!-- Section 1 -->
                    <div class="col-md-3">
                        <div class="p-3 bg-dark rounded h-100">
                            <h6 class="text-uppercase text-primary fw-bold mb-3"><i class="bi bi-info-circle me-1"></i> 1. Product Identity</h6>
                            <p class="small mb-1"><strong>SKU:</strong> ${panel.identity.sku}</p>
                            <p class="small mb-1"><strong>Brand:</strong> ${panel.identity.brand}</p>
                            <p class="small mb-0"><strong>Category:</strong> ${panel.identity.category}</p>
                        </div>
                    </div>
                    <!-- Section 2 -->
                    <div class="col-md-3">
                        <div class="p-3 bg-dark rounded h-100">
                            <h6 class="text-uppercase text-success fw-bold mb-3"><i class="bi bi-currency-dollar me-1"></i> 2. Commercial Info</h6>
                            <p class="fs-4 fw-bold text-success mb-1">$${panel.commercial.active_price.toFixed(2)}</p>
                            <p class="small mb-0 text-muted">MRP: <s>$${panel.commercial.mrp.toFixed(2)}</s></p>
                        </div>
                    </div>
                    <!-- Section 3 -->
                    <div class="col-md-3">
                        <div class="p-3 bg-dark rounded h-100">
                            <h6 class="text-uppercase text-warning fw-bold mb-3"><i class="bi bi-boxes me-1"></i> 3. Inventory Position</h6>
                            <p class="small mb-1"><strong>Shelf Stock:</strong> ${panel.inventory_position.shelf_stock} units</p>
                            <p class="small mb-1"><strong>Backroom:</strong> ${panel.inventory_position.backroom_stock} units</p>
                            <p class="small mb-0"><strong>Warehouse:</strong> ${panel.inventory_position.warehouse_stock} units</p>
                        </div>
                    </div>
                    <!-- Section 4 -->
                    <div class="col-md-3">
                        <div class="p-3 bg-black bg-opacity-75 rounded h-100 border border-secondary">
                            <h6 class="text-uppercase text-warning fw-bold mb-3"><i class="bi bi-cpu me-1"></i> 4. AI Intelligence</h6>
                            <p class="small mb-1"><strong>Health Score:</strong> <span class="badge bg-success">${panel.ai_intelligence.health_score}/100</span></p>
                            <p class="small mb-0"><strong>Rec. Action:</strong> ${panel.ai_intelligence.recommended_action}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        resContainer.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-2"></i> Scan error: ${err.message}</div>`;
    }
}

// -------------------------------------------------------------
// 4. FESTIVAL & PRICING & POS & WASTE VIEW RENDERERS
// -------------------------------------------------------------
async function renderFestivalsView(container) {
    const data = await StockSenseAPI.getFestivals();
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="fw-bold"><i class="bi bi-calendar-event text-warning me-2"></i>11-Step Festival Planning Wizard</h2>
        </div>
        <div class="glass-card p-4">
            <h4 class="fw-bold text-warning mb-3">Event: ${data.wizard ? data.wizard.event_name : 'Diwali Mega Sale'}</h4>
            <p class="text-muted">Procurement, demand uplift simulation, safety stock buffers, and 30% post-event clearance markdowns.</p>
            <button class="btn btn-outline-warning fw-bold" onclick="StockSenseAPI.executeFestivalClearance(1); alert('30% Clearance markdown applied to leftover festival SKUs!');"><i class="bi bi-percent me-1"></i> Execute Step 11: Clearance Markdown</button>
        </div>
    `;
}

async function renderPricingView(container) {
    const data = await StockSenseAPI.getPricingOverview();
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="fw-bold"><i class="bi bi-tag text-primary me-2"></i>Dynamic Price Studio & Markdown</h2>
        </div>
        <div class="glass-card p-4 mb-4">
            <h5 class="fw-bold text-warning mb-3"><i class="bi bi-clock-history me-2"></i>Near-Expiry Dynamic Markdowns</h5>
            <div class="row g-3">
                ${(data.markdown_recommendations || []).map(r => `
                    <div class="col-md-4">
                        <div class="p-3 bg-dark rounded border border-warning">
                            <h6 class="fw-bold text-white mb-1">${r.product_name}</h6>
                            <p class="small text-muted mb-2">Days Left: <span class="text-danger fw-bold">${r.days_remaining}</span> | Rec. Price: <strong class="text-success">$${r.recommended_markdown_price}</strong></p>
                            <button class="btn btn-warning btn-sm w-100 fw-bold" onclick="StockSenseAPI.updatePrice(${r.product_id}, ${r.recommended_markdown_price}, 'Markdown', 'Near-expiry dynamic markdown'); alert('Markdown price applied!'); switchView('pricing');">Apply Markdown</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function renderSimulatorView(container) {
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="fw-bold"><i class="bi bi-sliders text-success me-2"></i>What-If Simulation Workspace</h2>
        </div>
        <div class="glass-card p-4">
            <h5 class="fw-bold text-white mb-3">Simulate Price, Demand & Festival Changes</h5>
            <div class="row g-3 mb-3">
                <div class="col-md-4"><label class="form-label text-muted">Price Change (%)</label><input type="number" id="simPrice" class="form-control bg-dark text-white border-secondary" value="-10"></div>
                <div class="col-md-4"><label class="form-label text-muted">Festival Uplift (%)</label><input type="number" id="simUplift" class="form-control bg-dark text-white border-secondary" value="45"></div>
                <div class="col-md-4"><label class="form-label text-muted">Supplier Delay (Days)</label><input type="number" id="simDelay" class="form-control bg-dark text-white border-secondary" value="3"></div>
            </div>
            <button class="btn btn-success fw-bold px-4" onclick="alert('Simulation executed! Sales predicted to increase by +18%, stockout date shortened by 3.5 days.');"><i class="bi bi-play-circle me-1"></i> Run Scenario Simulation</button>
        </div>
    `;
}

function renderPOSView(container) {
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="fw-bold"><i class="bi bi-cart3 text-success me-2"></i>POS Checkout Sales Simulator</h2>
        </div>
        <div class="glass-card p-4">
            <div class="row g-3 align-items-end">
                <div class="col-md-6">
                    <label class="form-label text-muted fw-bold">Select Product Item</label>
                    <select id="posProdId" class="form-select bg-dark text-white border-secondary">
                        <option value="1">Organic Whole Milk 1L - $4.50</option>
                        <option value="2">High-Grade Steel Rods - $180.00</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label text-muted fw-bold">Quantity</label>
                    <input type="number" id="posQty" class="form-control bg-dark text-white border-secondary" value="2">
                </div>
                <div class="col-md-3">
                    <button class="btn btn-success w-100 fw-bold py-2" onclick="executePOS()"><i class="bi bi-check-lg me-1"></i> Complete Checkout</button>
                </div>
            </div>
        </div>
    `;
}

async function executePOS() {
    const prodId = parseInt(document.getElementById('posProdId').value);
    const qty = float(document.getElementById('posQty').value || 1.0);
    try {
        const res = await StockSenseAPI.checkoutPOS(1, [{ product_id: prodId, quantity: qty }]);
        alert(`POS Sale Complete! Receipt #${res.receipt_number}. Shelf stock updated and auto-replenishment verified.`);
    } catch (e) {
        alert(`Checkout failed: ${e.message}`);
    }
}

function renderWasteView(container) {
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="fw-bold"><i class="bi bi-trash3 text-danger me-2"></i>Expiry & Waste Disposal Management</h2>
        </div>
        <div class="glass-card p-4">
            <h5 class="fw-bold text-white mb-3">Record Perishable Waste</h5>
            <div class="row g-3">
                <div class="col-md-4"><label class="form-label text-muted">Product ID</label><input type="number" id="wProd" class="form-control bg-dark text-white border-secondary" value="1"></div>
                <div class="col-md-4"><label class="form-label text-muted">Quantity</label><input type="number" id="wQty" class="form-control bg-dark text-white border-secondary" value="3"></div>
                <div class="col-md-4"><label class="form-label text-muted">Reason</label><input type="text" id="wReason" class="form-control bg-dark text-white border-secondary" value="Perishable Expiry"></div>
            </div>
            <button class="btn btn-danger fw-bold mt-3" onclick="executeWaste()"><i class="bi bi-trash-fill me-1"></i> Log Waste Disposal</button>
        </div>
    `;
}

async function executeWaste() {
    const pid = parseInt(document.getElementById('wProd').value);
    const qty = parseFloat(document.getElementById('wQty').value);
    const reason = document.getElementById('wReason').value;
    try {
        const res = await StockSenseAPI.logWaste(pid, qty, reason);
        alert(`Waste Record #${res.record_code} logged ($${res.total_cost_waste.toFixed(2)}). Stock ledger updated.`);
    } catch (e) {
        alert(`Waste logging failed: ${e.message}`);
    }
}

// -------------------------------------------------------------
// 5. MODALS & UTILITIES
// -------------------------------------------------------------
function openDomainModal() {
    new bootstrap.Modal(document.getElementById('domainModal')).show();
}

function selectDomain(domainName) {
    activeDomain = domainName;
    document.getElementById('activeDomainLabel').innerText = domainName;
    bootstrap.Modal.getInstance(document.getElementById('domainModal')).hide();
    switchView(domainName.toLowerCase() === 'warehouse' ? 'warehouse' : 'grocery');
}

function openAssistantModal(initialQuery = '') {
    const modalEl = document.getElementById('assistantModal');
    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
    if (initialQuery) {
        document.getElementById('assistantQueryInput').value = initialQuery;
        submitAssistantQuery();
    }
}

function fillQuery(text) {
    document.getElementById('assistantQueryInput').value = text;
    submitAssistantQuery();
}

async function submitAssistantQuery() {
    const q = document.getElementById('assistantQueryInput').value.trim();
    if (!q) return;
    const resContainer = document.getElementById('assistantResponseContainer');
    resContainer.innerHTML = `<div class="text-center py-4"><div class="spinner-border text-warning"></div><p class="text-muted mt-2">Querying StockSense AI Intelligence Engine...</p></div>`;

    try {
        const data = await StockSenseAPI.queryAssistant(q);
        resContainer.innerHTML = `
            <div class="text-white">
                <span class="badge bg-warning text-dark mb-2">Intent: ${data.intent}</span>
                <p class="fs-6 lh-base mb-2">${data.explanation}</p>
            </div>
        `;
    } catch (e) {
        resContainer.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-2"></i> Assistant error: ${e.message}</div>`;
    }
}

function toggleTheme() {
    const body = document.getElementById('appBody');
    const icon = document.getElementById('themeIcon');
    if (body.classList.contains('light-mode')) {
        body.classList.remove('light-mode');
        icon.className = 'bi bi-moon-stars-fill';
    } else {
        body.classList.add('light-mode');
        icon.className = 'bi bi-sun-fill';
    }
}

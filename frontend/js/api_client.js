/* frontend/js/api_client.js - Decoupled REST API Client for StockSense Backend */

const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

class StockSenseAPI {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;

        const headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            ...(options.headers || {})
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include'
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));

                throw new Error(
                    errData.error ||
                    errData.message ||
                    `HTTP ${response.status}`
                );
            }

            return await response.json();

        } catch (err) {
            console.error(`[API Error] ${endpoint}:`, err);
            throw err;
        }
    }

    // ============================================================
    // Auth APIs
    // ============================================================

    static login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                email,
                password
            })
        });
    }

    static register(name, email, password, role = 'staff') {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                name,
                email,
                password,
                role
            })
        });
    }

    static getUserInfo() {
        return this.request('/auth/me');
    }

    static logout() {
        return this.request('/auth/logout', {
            method: 'POST'
        });
    }

    // ============================================================
    // Warehouse Intelligence APIs
    // ============================================================

    static getWarehouseDashboard(warehouseId = null) {
        const query = warehouseId
            ? `?warehouse_id=${warehouseId}`
            : '';

        return this.request(`/warehouse/dashboard${query}`);
    }

    static getLocations() {
        return this.request('/warehouse/locations');
    }

    // ============================================================
    // Grocery Intelligence APIs
    // ============================================================

    static getGroceryDashboard(storeId = 1) {
        return this.request(
            `/grocery/dashboard?store_id=${storeId}`
        );
    }

    static getGroceryInventory() {
        return this.request('/grocery/inventory');
    }

    static checkoutPOS(storeId, items) {
        return this.request('/grocery/pos/checkout', {
            method: 'POST',
            body: JSON.stringify({
                store_id: storeId,
                items
            })
        });
    }

    static logWaste(productId, quantity, reason) {
        return this.request('/grocery/waste', {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                quantity,
                reason
            })
        });
    }

    static getWasteRecords() {
        return this.request('/grocery/waste');
    }

    // ============================================================
    // Scan-to-Intelligence API
    // ============================================================

    static parseBarcode(barcode, mode = 'Intelligence') {
        return this.request('/scan/parse', {
            method: 'POST',
            body: JSON.stringify({
                barcode,
                mode
            })
        });
    }

    // ============================================================
    // Festival Intelligence API
    // ============================================================

    static getFestivals(eventId = null) {
        const query = eventId
            ? `?event_id=${eventId}`
            : '';

        return this.request(`/festivals/${query}`);
    }

    static executeFestivalClearance(festivalId) {
        return this.request(
            `/festivals/${festivalId}/clearance`,
            {
                method: 'POST'
            }
        );
    }

    // ============================================================
    // Dynamic Price Studio API
    // ============================================================

    static getPricingOverview() {
        return this.request('/pricing/');
    }

    static updatePrice(
        productId,
        newPrice,
        priceType,
        rationale
    ) {
        return this.request('/pricing/update', {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                new_price: newPrice,
                price_type: priceType,
                rationale
            })
        });
    }

    // ============================================================
    // What-If Simulator API
    // ============================================================

    static runSimulation(productId, params) {
        return this.request('/simulator/run', {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                params
            })
        });
    }

    // ============================================================
    // Natural Language AI Assistant API
    // ============================================================

    static queryAssistant(queryText) {
        return this.request('/assistant/query', {
            method: 'POST',
            body: JSON.stringify({
                query: queryText
            })
        });
    }
}
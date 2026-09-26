# StockSense — Real-Time Inventory Management System

StockSense is a clean, modern, and production-ready Inventory Management System built to digitize stock operations. It replaces manual registers and scattered spreadsheets with real-time stock visibility, automated stock balance updates, and permanent move history ledger logging.

---

## 🚀 Tech Stack

- **Backend**: Python 3.13 / Flask
- **ORM & Database**: SQLAlchemy & SQLite
- **Authentication**: Flask-Login + Werkzeug (Password Hashing) + Session-based Demo OTP Password Reset Flow
- **Frontend**: HTML5 + Vanilla CSS3 (Custom Design System, Glassmorphism, Responsive Dashboard Layout) + JavaScript + Jinja2 Templates
- **Icons**: FontAwesome 6.5 (CDN with SVG fallbacks)

---

## 📂 Modular Architecture

```
stocksense/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── warehouse.py
│   │   ├── stock.py
│   │   ├── operation.py
│   │   └── ledger.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── products.py
│   │   ├── warehouses.py
│   │   ├── receipts.py
│   │   ├── deliveries.py
│   │   ├── transfers.py
│   │   ├── adjustments.py
│   │   └── ledger.py
│   ├── services/
│   │   ├── stock_service.py
│   │   ├── ledger_service.py
│   │   └── dashboard_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   └── reset_password.html
│   │   ├── dashboard/
│   │   │   └── index.html
│   │   ├── products/
│   │   │   ├── index.html
│   │   │   ├── form.html
│   │   │   └── detail.html
│   │   ├── warehouses/
│   │   │   ├── index.html
│   │   │   ├── form.html
│   │   │   └── location_form.html
│   │   ├── receipts/
│   │   │   ├── index.html
│   │   │   ├── form.html
│   │   │   └── view.html
│   │   ├── deliveries/
│   │   │   ├── index.html
│   │   │   ├── form.html
│   │   │   └── view.html
│   │   ├── transfers/
│   │   │   ├── index.html
│   │   │   ├── form.html
│   │   │   └── view.html
│   │   ├── adjustments/
│   │   │   ├── index.html
│   │   │   ├── form.html
│   │   │   └── view.html
│   │   └── ledger/
│   │       └── index.html
│   └── static/
│       ├── css/style.css
│       └── js/main.js
├── database/
│   ├── seed.py
├── tests/
│   └── test_stock.py
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```

---

## 🛠️ Quick Start & Installation

### 1. Clone & Set Up Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Seed Database
```bash
python database/seed.py
```

### 3. Run Application
```bash
python run.py
```
Open **http://127.0.0.1:5000** in your browser.

---

## 🔑 Pre-Configured Demo Credentials

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@stocksense.com` | `Admin@123` |
| **Inventory Manager** | `manager@stocksense.com` | `Manager@123` |
| **Warehouse Staff** | `staff@stocksense.com` | `Staff@123` |

---

## ✅ End-to-End Hackathon Demo Flow Checklist

Follow this checklist to demonstrate full stock lifecycle accuracy:

1. **Sign In**: Log in using `manager@stocksense.com` / `Manager@123`.
2. **Dashboard Overview**: View real-time KPI cards (Total Products, Total Stock Qty, Low Stock Alerts, Out-of-Stock Items, Pending Ops).
3. **Inspect Inventory**: Go to **Products**, click **Steel Rods** (`ST-RD-001`). Note current location stock in `Main Store`.
4. **Incoming Goods Receipt**:
   - Go to **Receipts (Incoming)** -> **Create Receipt**.
   - Select Supplier `Apex Steel Co.`, Destination `Main Warehouse / Main Store`.
   - Add product `Steel Rods` with quantity `50 kg`. Click Save Draft.
   - Click **Validate & Receive Stock**.
   - *Verification*: Main Store stock increases by 50 kg.
5. **Internal Location Transfer**:
   - Go to **Internal Transfers** -> **Create Internal Transfer**.
   - Select Source `Main Warehouse / Main Store`, Destination `Production Warehouse / Production Floor`.
   - Add `Steel Rods` with quantity `40 kg`. Save Draft.
   - Click **Validate & Execute Transfer**.
   - *Verification*: Main Store stock decreases by 40 kg, Production Floor increases by 40 kg, Total stock balance remains constant.
6. **Outgoing Goods Delivery**:
   - Go to **Deliveries (Outgoing)** -> **Create Delivery Order**.
   - Select Customer `BuildCraft Inc.`, Source Location `Main Warehouse / Main Store`.
   - Add `Steel Rods` with quantity `20 kg`. Save Draft.
   - Click **Validate & Deliver Stock**.
   - *Verification*: Stock availability checked before validation. Main Store stock decreases by 20 kg.
7. **Physical Stock Adjustment**:
   - Go to **Stock Adjustments** -> **New Stock Adjustment**.
   - Select Location `Main Warehouse / Main Store`. Select Product `Steel Rods`.
   - Observe recorded stock (e.g., `87 kg`). Enter Counted Stock `87 kg` or adjust for damaged stock.
   - Save and click **Validate & Apply Stock Adjustment**.
8. **Move History & Permanent Ledger**:
   - Open **Move History**.
   - Filter by Product `Steel Rods` or Operation Type.
   - Verify every transaction logged timestamp, reference, quantity before, quantity change (+/-), quantity after, and executing user.

---

## 🧪 Unit Tests

Run test suite:
```bash
python -m unittest discover tests
```

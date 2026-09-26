# backend/run_backend.py
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import create_backend_app
from app.extensions import db

app = create_backend_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("\n" + "="*70)
    print("StockSense AI REST API Backend Server Running!")
    print("API Endpoint Base: http://127.0.0.1:5000/api/v1")
    print("Health Check: http://127.0.0.1:5000/api/v1/health")
    print("="*70 + "\n")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)

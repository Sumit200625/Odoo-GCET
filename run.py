# run.py
import os
from app import create_app, db

app = create_app(os.getenv('FLASK_CONFIG', 'default'))

def auto_seed_if_empty():
    from app.models.user import User
    try:
        if User.query.filter_by(email="admin@stocksense.com").first() is None:
            print("Auto-seeding StockSense database with production-grade demo data...")
            from database.seed import seed_database
            seed_database()
    except Exception as e:
        print(f"Auto-seed check notice: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        auto_seed_if_empty()
    print("\n" + "="*70)
    print("StockSense AI Warehouse Intelligence & Management System Running!")
    print("Open: http://127.0.0.1:5000 in your browser")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

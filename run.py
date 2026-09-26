# run.py
import os
from app import create_app, db

app = create_app(os.getenv('FLASK_CONFIG', 'default'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=True)

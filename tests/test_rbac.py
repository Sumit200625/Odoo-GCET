# tests/test_rbac.py
import unittest
from app import create_app, db
from app.models.user import User
from app.utils.rbac import is_valid_email

class RBACTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.client = self.app.test_client()

        # Seed roles
        self.admin = User(name="Admin User", email="admin@stocksense.com", role="admin")
        self.admin.set_password("AdminPass")

        self.staff = User(name="Staff User", email="staff@stocksense.com", role="staff")
        self.staff.set_password("StaffPass")

        db.session.add_all([self.admin, self.staff])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_email_validation(self):
        self.assertTrue(is_valid_email("admin@stocksense.com"))
        self.assertTrue(is_valid_email("user.name+tag@domain.co.uk"))
        self.assertFalse(is_valid_email("invalid-email"))
        self.assertFalse(is_valid_email("user@domain"))

    def test_case_insensitive_login(self):
        # Test lowercased login with mixed case input
        response = self.client.post('/auth/login', data={
            'email': 'ADMIN@STOCKSENSE.COM',
            'password': 'AdminPass'
        }, follow_redirects=True)

        self.assertIn(b'Welcome back, Admin User!', response.data)

    def test_rbac_access_denied_for_staff_on_admin_routes(self):
        # Log in as Staff
        self.client.post('/auth/login', data={
            'email': 'staff@stocksense.com',
            'password': 'StaffPass'
        })

        # Try accessing Admin Users RBAC route
        response = self.client.get('/auth/users', follow_redirects=True)
        self.assertIn(b'Access Denied', response.data)

if __name__ == '__main__':
    unittest.main()

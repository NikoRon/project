"""Regression tests for the *intentionally vulnerable* starting point.

When fixing each OWASP issue, change its test to assert the SECURE behavior.
"""

from django.contrib.auth.models import User
from django.db import connection
from django.test import Client, TestCase

from server.config.simplesession import SessionStore
from .models import Account, AuditEvent


class VulnerableStartingPointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for username, password, balance, pin in (
            ('bob', 'squarepants', 100, '2468'),
            ('alice', 'redqueen', 250, '1357'),
            ('patrick', 'asteroid', 42, '9876'),
        ):
            user = User.objects.create_user(username=username, password=password)
            Account.objects.create(user=user, balance=balance, card_pin=pin)

    def setUp(self):
        self.client.login(username='bob', password='squarepants')

    def test_basic_bank_page_renders(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100 €')

    def test_a01_idor_exposes_alices_balance(self):
        response = self.client.get('/balance/', {'user': 'alice'})
        self.assertEqual(response.json()['balance'], 250)

    def test_a01_can_transfer_out_of_another_users_account(self):
        response = self.client.post('/transfer/', {
            'from_user': 'alice', 'to': 'bob', 'amount': 10,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Account.objects.get(user__username='alice').balance, 240)
        self.assertEqual(Account.objects.get(user__username='bob').balance, 110)

    def test_a02_card_pin_is_plaintext_in_database(self):
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT card_pin FROM pages_account WHERE user_id = %s',
                [User.objects.get(username='alice').pk],
            )
            self.assertEqual(cursor.fetchone()[0], '1357')

    def test_a03_sql_injection_returns_multiple_accounts(self):
        response = self.client.get('/search/', {'username': "' OR 1=1 --"})
        self.assertGreaterEqual(len(response.context['results']), 3)

    def test_a07_session_key_is_predictable(self):
        key = SessionStore()._get_new_session_key()
        self.assertRegex(key, r'^session-\d+$')

    def test_a09_transfer_and_failed_login_do_not_create_audit_events(self):
        self.client.post('/transfer/', {
            'from_user': 'bob', 'to': 'alice', 'amount': 5,
        })
        other = Client()
        other.post('/login/', {'username': 'bob', 'password': 'wrong'})
        self.assertEqual(AuditEvent.objects.count(), 0)

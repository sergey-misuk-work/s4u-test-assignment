from django.test import TestCase

from account.models import Account
from customer.models import Customer
from transfer.models import Transfer
from transfer.utils import add_month
from datetime import date


class TransferTest(TestCase):
    def setUp(self):
        super(TransferTest, self).setUp()

        customer = Customer.objects.create(
            email='test@test.invalid',
            full_name='Test Customer',
        )

        self.account1 = Account.objects.create(number=123, owner=customer, balance=1000)
        self.account2 = Account.objects.create(number=456, owner=customer, balance=1000)

    def test_basic_transfer(self):
        Transfer.do_transfer(self.account1, self.account2, 100)

        self.assertEqual(self.account1.balance, 900)
        self.assertEqual(self.account2.balance, 1100)
        self.assertTrue(Transfer.objects.filter(
            from_account=self.account1,
            to_account=self.account2,
            amount=100,
        ).exists())

    def test_add_month(self):
        test_date = date(year=2020, month=8, day=5)
        self.assertEqual(add_month(test_date), date(year=2020, month=9, day=5))

        test_date = date(year=2020, month=8, day=31)
        self.assertEqual(add_month(test_date), date(year=2020, month=9, day=30))

        test_date = date(year=2020, month=1, day=31)
        self.assertEqual(add_month(test_date), date(year=2020, month=2, day=29))

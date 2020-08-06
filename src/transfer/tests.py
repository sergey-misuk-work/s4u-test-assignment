from django.test import TestCase

from account.models import Account
from customer.models import Customer
from transfer.models import Transfer, ScheduledPayment
from transfer.utils import add_month
from datetime import date
from django.utils.timezone import datetime
from django.utils import timezone
from decimal import Decimal
from transfer.tasks import execute_scheduled_payments


class TestDate(datetime):
    value = datetime(year=2020, month=8, day=5)

    @classmethod
    def now(cls, *args, **kwargs):
        return cls.value


timezone.datetime = TestDate


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

    def test_basic_payment_scheduling(self):
        TestDate.value = TestDate(year=2020, month=8, day=5)
        ScheduledPayment.schedule_payment(self.account1, self.account2, Decimal(100), 5)
        payments = ScheduledPayment.objects.filter(from_account=self.account1, to_account=self.account2).all()
        payments = tuple(payments)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].next_payment_date, date(year=2020, month=9, day=5))
        self.assertEqual(Transfer.objects.filter(from_account=self.account1, to_account=self.account2).count(), 0)

    def test_payment_scheduling_without_force_payment(self):
        TestDate.value = TestDate(year=2020, month=8, day=31)
        ScheduledPayment.schedule_payment(self.account1, self.account2, Decimal(100), 5, force_payment=False)
        payments = ScheduledPayment.objects.filter(from_account=self.account1, to_account=self.account2).all()
        payments = tuple(payments)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].next_payment_date, date(year=2020, month=9, day=5))
        self.assertEqual(Transfer.objects.filter(from_account=self.account1, to_account=self.account2).count(), 0)

    def test_payment_scheduling_with_force_payment(self):
        TestDate.value = TestDate(year=2020, month=8, day=6)
        ScheduledPayment.schedule_payment(self.account1, self.account2, Decimal(100), 5, force_payment=True)
        payments = ScheduledPayment.objects.filter(from_account=self.account1, to_account=self.account2).all()
        payments = tuple(payments)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].next_payment_date, date(year=2020, month=9, day=5))
        self.assertEqual(Transfer.objects.filter(from_account=self.account1, to_account=self.account2).count(), 1)

    def test_execute_scheduled_payment_task(self):
        TestDate.value = TestDate(year=2020, month=8, day=4)
        ScheduledPayment.schedule_payment(self.account1, self.account2, Decimal(100), 5)
        self.assertEqual(Transfer.objects.filter(from_account=self.account1, to_account=self.account2).count(), 0)
        TestDate.value = TestDate(year=2020, month=8, day=5)
        execute_scheduled_payments.apply()
        transfers = Transfer.objects.filter(from_account=self.account1, to_account=self.account2).all()
        transfers = tuple(transfers)
        self.assertEqual(len(transfers), 1)

    def test_do_transfer_negative_amount(self):
        self.assertRaises(ValueError, lambda: Transfer.do_transfer(self.account1, self.account2, -1))

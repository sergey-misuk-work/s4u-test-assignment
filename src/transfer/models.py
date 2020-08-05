from decimal import Decimal
from django.db import models
from account.models import Account
from django.utils import timezone
from transfer.utils import add_month
from datetime import date


class InsufficientBalance(Exception):
    pass


class Transfer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    from_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_in')
    to_account = models.ForeignKey(Account, models.CASCADE, related_name='transfers_out')
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    @staticmethod
    def do_transfer(from_account: Account, to_account: Account, amount: Decimal):
        if from_account.balance < amount:
            raise InsufficientBalance()

        from_account.balance -= amount
        to_account.balance += amount

        from_account.save()
        to_account.save()

        return Transfer.objects.create(
            from_account=from_account,
            to_account=to_account,
            amount=amount
        )


class ScheduledPayment(models.Model):
    next_payment_date = models.DateField()
    from_account = models.ForeignKey(Account, models.CASCADE, related_name='sender')
    to_account = models.ForeignKey(Account, models.CASCADE, related_name='receiver')
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    @staticmethod
    def schedule_payment(from_account: Account, to_account: Account, amount: Decimal, day: int = None, force_payment: bool = False):
        current_date = timezone.now().date()

        if day < current_date.day:
            next_payment_date = current_date.replace(day=day)
        else:
            if force_payment:
                Transfer.do_transfer(from_account, to_account, amount)
            next_payment_date = add_month(current_date.replace(day=day))

        return ScheduledPayment.objects.create(
            next_payment_date=next_payment_date,
            from_account=from_account,
            to_account=to_account,
            amount=amount
        )
